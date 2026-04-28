#!/usr/bin/env -S deno run
'use strict';

// ym.js - "minus minus" YAML-like parser and formatter
// Usage (CLI): node ym.js < input.yaml
// version: 0.1.5

// ---------- helpers ----------

const YAML_SPECIAL = /[:{}[\],&*#?|\-<>=!%@~]/;

function getIndent(line) {
    return line.match(/^(\s*)/)[1].length;
}

function stripQuotes(s) {
    if (!s)
        return s;
    if (s[0] === "'")
        return s.replace(/^'|'$/g, '').replace(/''/g, "'");
    if (s[0] === '"')
        return s.replace(/^"|"$/g, '').replace(/\\"/g, '"').replace(/\\n/g, '\n').replace(/\\t/g, '\t').replace(/\\\\/g, '\\');
    return s;
}

function quoteIfNeeded(s) {
    if (typeof s !== "string") return s;
    if (s === "") return '""';
    if (!YAML_SPECIAL.test(s)) return s;
    const escaped = s.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\t/g, "\\t").replace(/\n/g, "\\n");
    return `"${escaped}"`;
}

// ---------- inline comment detection ----------

// Extract inline comment from a scalar value string (raw, before stripQuotes).
// Returns { value, comment } where comment may be null.
function extractInlineComment(raw) {
    // quoted value followed by whitespace and #
    const quotedMatch = raw.match(/^((?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'))\s+(#.*)$/);
    if (quotedMatch) return { value: quotedMatch[1], comment: quotedMatch[2] };

    // unquoted value containing ' #'
    if (!raw.startsWith('"') && !raw.startsWith("'")) {
        const unquotedMatch = raw.match(/^(.*?)\s+(#.*)$/);
        if (unquotedMatch) return { value: unquotedMatch[1], comment: unquotedMatch[2] };
    }

    return { value: raw, comment: null };
}

// ---------- parser helpers ----------

function parseBlockScalar(lines, idx, baseIndent) {
    // collect lines for a |- block scalar
    const parts = [];
    while (idx < lines.length) {
        const line = lines[idx];
        const trimmed = line.trim();
        const indent = getIndent(line);
        if (!trimmed) {
            parts.push('');
            idx++;
            continue;
        }
        if (indent > baseIndent) {
            parts.push(trimmed);
            idx++;
        } else {
            break;
        }
    }
    // |- strips trailing newlines
    while (parts.length && parts[parts.length - 1] === '') parts.pop();
    return [parts.join('\n'), idx];
}

function parseContinuation(lines, idx, baseIndent, firstLine) {
    // collect implicit continuation lines after a string value, joined with space
    const parts = [firstLine];
    while (idx < lines.length) {
        const line = lines[idx];
        const trimmed = line.trim();
        if (!trimmed) break;
        const indent = getIndent(line);
        if (indent > baseIndent) {
            parts.push(trimmed);
            idx++;
        } else {
            break;
        }
    }
    return [parts.join(' '), idx];
}

function parseListValue(lines, idx, arrIndent, baseIndent, commentCount) {
    // parse a list, allowing comment lines mid-list
    // returns [items, commentsSoFar, idx]
    // comments are returned as { key, value } to be inserted in the parent obj
    const items = [];
    const comments = [];
    while (idx < lines.length) {
        const line = lines[idx];
        const trimmed = line.trim();
        if (!trimmed) { idx++; continue; }
        const indent = getIndent(line);

        // comments may appear at any indent level (including unindented) mid-list
        if (trimmed.startsWith('#')) {
            const commentLines = [];
            while (idx < lines.length) {
                const l = lines[idx];
                const t = l.trim();
                if (!t) break;
                if (!t.startsWith('#')) break;
                commentLines.push(t);
                idx++;
            }
            const ck = `__#${commentCount}.${items.length}`;
            comments.push({ key: ck, value: commentLines.join('\n') });
            commentCount++;
            continue;
        }

        if (indent < arrIndent) break;
        if (indent > arrIndent) { idx++; continue; }

        if (!trimmed.startsWith('- ') && trimmed !== '-') break;
        const rawItem = trimmed.slice(2).trim();
        const { value: itemValue, comment: itemComment } = extractInlineComment(rawItem);
        if (itemComment) {
            const ck = `__#${commentCount}.${items.length}`;
            comments.push({ key: ck, value: itemComment });
            commentCount++;
        }
        items.push(stripQuotes(itemValue));
        idx++;
    }
    return [items, comments, commentCount, idx];
}

function parseEmptyValue(lines, idx, baseIndent, commentCount) {
    // skip blank lines
    while (idx < lines.length && !lines[idx].trim()) idx++;

    if (idx >= lines.length) return { value: '', commentCount, idx };

    const nextLine = lines[idx];
    const nextTrimmed = nextLine.trim();
    const nextIndent = getIndent(nextLine);

    // accept lists at same indent level (unindented) or deeper
    const isList = nextTrimmed.startsWith('- ') || nextTrimmed === '-';
    if (isList && nextIndent >= baseIndent) {
        const [items, comments, newCount, newIdx] = parseListValue(lines, idx, nextIndent, baseIndent, commentCount);
        return { value: { isList: true, items, comments }, commentCount: newCount, idx: newIdx };
    }

    if (nextIndent <= baseIndent) return { value: '', commentCount, idx };

    // nested dict
    const [obj, newIdx, newCount] = parseBlock(lines, idx, nextIndent, commentCount);
    return { value: obj, commentCount: newCount, idx: newIdx };
}

// ---------- main parser ----------

function parseBlock(lines, idx, baseIndent, commentCount = 0) {
    const obj = {};

    while (idx < lines.length) {
        const line = lines[idx];
        const trimmed = line.trim();

        if (!trimmed) { idx++; continue; }

        const indent = getIndent(line);
        if (indent < baseIndent && !trimmed.startsWith('#')) break;
        if (indent > baseIndent) { idx++; continue; }

        // comment block
        if (trimmed.startsWith('#')) {
            const commentLines = [];
            while (idx < lines.length) {
                const l = lines[idx];
                const t = l.trim();
                if (!t) break;
                const li = getIndent(l);
                if ((li !== baseIndent && li !== 0) || !t.startsWith('#')) break;
                commentLines.push(t);
                idx++;
            }
            const ck = `__#${commentCount++}`;
            obj[ck] = commentLines.join('\n');
            continue;
        }

        // key: value
        const m = trimmed.match(/^([\w][\w ./-]*?)\s*:\s*(.*)$/);
        if (!m) { idx++; continue; }

        const key = m[1].trim();
        let value = m[2].trim();
        idx++;

        if (value === '|-') {
            [value, idx] = parseBlockScalar(lines, idx, baseIndent);
        } else if (value === '[]') {
            value = [];
        } else if (value === '') {
            const result = parseEmptyValue(lines, idx, baseIndent, commentCount);
            idx = result.idx;
            commentCount = result.commentCount;
            const r = result.value;
            if (r && typeof r === 'object' && r.isList) {
                for (const c of r.comments) obj[c.key] = c.value;
                value = r.items;
            } else {
                value = r;
            }
        } else {
            const { value: rawValue, comment } = extractInlineComment(value);
            if (comment) {
                obj[`__#${commentCount++}`] = comment;
            }
            value = stripQuotes(rawValue);
            [value, idx] = parseContinuation(lines, idx, baseIndent, value);
        }

        obj[key] = value;
    }

    return [obj, idx, commentCount];
}

export function parse(text) {
    const lines = text.split('\n');
    const [obj] = parseBlock(lines, 0, 0);
    return obj;
}

// ---------- formatter ----------

function formatComment(obj, key, prefix) {
    const lines = [];
    for (const cl of obj[key].split('\n'))
        lines.push(prefix + cl);
    return lines;
}

function formatArray(obj, key, value, prefix, indent) {
    const lines = [];
    if (value.length === 0) {
        lines.push(`${prefix}${key}: []`);
        return lines;
    }
    lines.push(`${prefix}${key}:`);
    // gather list comments keyed as __#N.itemIndex
    const listComments = {};
    for (const k of Object.keys(obj)) {
        const lm = k.match(/^__#\d+\.(\d+)$/);
        if (!lm) continue;
        const ii = parseInt(lm[1]);
        if (!listComments[ii]) listComments[ii] = [];
        listComments[ii].push(obj[k]);
    }
    for (let i = 0; i < value.length; i++) {
        if (listComments[i] !== undefined) {
            for (const entry of listComments[i])
                for (const cl of entry.split('\n'))
                    lines.push(`${prefix}${cl}`);
        }
        lines.push(`${prefix}  - ${quoteIfNeeded(value[i])}`);
    }
    return lines;
}

function formatScalar(key, value, prefix) {
    const lines = [];
    if (typeof value === "string" && value.includes('\n')) {
        lines.push(`${prefix}${key}: |-`);
        for (const l of value.split('\n'))
            lines.push(`${prefix}  ${l}`);
    } else {
        lines.push(`${prefix}${key}: ${quoteIfNeeded(value) ?? ''}`);
    }
    return lines;
}

export function format(obj, indent = 0) {
    const prefix = "  ".repeat(indent);
    const lines = [];

    for (const key of Object.keys(obj)) {
        if (key.startsWith("__#")) {
            // list comments (e.g. __#3.0) are handled inside formatArray
            if (/^__#\d+\.\d+$/.test(key)) continue;
            lines.push(...formatComment(obj, key, prefix));
            continue;
        }
        const value = obj[key];
        if (Array.isArray(value)) {
            lines.push(...formatArray(obj, key, value, prefix, indent));
        } else if (value !== null && typeof value === "object") {
            lines.push(`${prefix}${key}:`);
            lines.push(format(value, indent + 1));
        } else {
            lines.push(...formatScalar(key, value, prefix));
        }
    }

    return lines.join('\n');
}

// ---------- CLI ----------

async function main() {
    let chunks = [];
    for await (const chunk of Deno.stdin.readable) chunks.push(chunk); // eslint-disable-line no-undef
    const allBytes = new Uint8Array(chunks.reduce((acc, c) => acc + c.length, 0));
    let offset = 0;
    for (const chunk of chunks) { allBytes.set(chunk, offset); offset += chunk.length; }
    const text = new TextDecoder().decode(allBytes);
    const obj = parse(text);
    // console.log(obj);
    console.log(format(obj));
}

if (import.meta.main) main(); // eslint-disable-line no-undef

// Issues:
//
// Not important right now: There's a subtle issue with the list comments
// indentation in `format` — they'll be emitted at `prefix` level (the key's
// level) rather than the item's indented level. This was pre-existing; fixing
// it would require knowing which list they belong to.
