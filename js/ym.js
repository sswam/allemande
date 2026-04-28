#!/usr/bin/env -S deno run
'use strict';

// ym.js - "minus minus" YAML-like parser and formatter
// Usage (CLI): node ym.js < input.yaml
// version: 0.1.1

// ---------- helpers ----------

const YAML_SPECIAL = /[:{}[\],&*#?|\-<>=!%@~]/;

function getIndent(line) {
    return line.match(/^(\s*)/)[1].length;
}

function stripQuotes(s) {
    if (s && (s[0] === '"' || s[0] === "'"))
        return s.replace(/^["']|["']$/g, '').replace(/\\/g, '');
    return s;
}

function quoteIfNeeded(s) {
    if (typeof s !== "string") return s;
    if (!YAML_SPECIAL.test(s)) return s;
    const escaped = s.replace(/\\/g, "\\\\").replace(/"/g, '\\"').replace(/\t/g, "\\t").replace(/\n/g, "\\n");
    return `"${escaped}"`;
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
        if (indent < arrIndent) break;
        if (indent > arrIndent) { idx++; continue; }

        if (trimmed.startsWith('#')) {
            // comment mid-list: key encodes comment index and next item index
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

        if (!trimmed.startsWith('- ') && trimmed !== '-') break;
        items.push(trimmed.slice(2).trim());
        idx++;
    }
    return [items, comments, commentCount, idx];
}

function parseEmptyValue(lines, idx, baseIndent, commentCount) {
    // NOTE: The heuristic to detect `[items, comments]` array result in
    // `parseEmptyValue` is a bit awkward - I noted this could be refactored
    // with a result object for clarity

    // skip blank lines
    while (idx < lines.length && !lines[idx].trim()) idx++;

    if (idx >= lines.length) return ['', commentCount, idx];

    const nextLine = lines[idx];
    const nextTrimmed = nextLine.trim();
    const nextIndent = getIndent(nextLine);

    if (nextIndent <= baseIndent) return ['', commentCount, idx];

    if (nextTrimmed.startsWith('- ') || nextTrimmed === '-') {
        const [items, comments, newCount, newIdx] = parseListValue(lines, idx, nextIndent, baseIndent, commentCount);
        return [[items, comments], newCount, newIdx];
    }

    // nested dict
    const [obj, newIdx] = parseBlock(lines, idx, nextIndent, commentCount);
    return [obj, commentCount, newIdx];
}

// ---------- main parser ----------

function parseBlock(lines, idx, baseIndent, commentCount = 0) {
    const obj = {};

    while (idx < lines.length) {
        const line = lines[idx];
        const trimmed = line.trim();

        if (!trimmed) { idx++; continue; }

        const indent = getIndent(line);
        if (indent < baseIndent) break;
        if (indent > baseIndent) { idx++; continue; }

        // comment block
        if (trimmed.startsWith('#')) {
            const commentLines = [];
            while (idx < lines.length) {
                const l = lines[idx];
                const t = l.trim();
                if (!t) break;
                if (getIndent(l) !== baseIndent || !t.startsWith('#')) break;
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
            let listResult;
            [listResult, commentCount, idx] = parseEmptyValue(lines, idx, baseIndent, commentCount);
            // listResult may be [items, comments] for arrays, or obj for dicts, or ''
            if (Array.isArray(listResult) && listResult.length === 2 && Array.isArray(listResult[1]) && listResult[1].length >= 0 && Array.isArray(listResult[0])) {
                const [items, comments] = listResult;
                // insert list-associated comments into obj before the key
                for (const c of comments) {
                    obj[c.key] = c.value;
                }
                value = items;
            } else {
                value = listResult;
            }
        } else {
            value = stripQuotes(value);
            [value, idx] = parseContinuation(lines, idx, baseIndent, value);
        }

        obj[key] = value;
    }

    return [obj, idx];
}

export function parse(text) {
    const lines = text.split('\n');
    const [obj] = parseBlock(lines, 0, 0);
    return obj;
}

// ---------- formatter ----------

export function format(obj, indent = 0) {
    const prefix = "  ".repeat(indent);
    const lines = [];

    for (const key of Object.keys(obj)) {
        if (key.startsWith("__#")) {
            // comment: check if it's a list comment (has a dot, e.g. __#3.0) — skip here, handled in array output
            if (/^__#\d+\.\d+$/.test(key)) continue;
            for (const cl of obj[key].split('\n'))
                lines.push(prefix + cl);
            continue;
        }
        const value = obj[key];
        if (Array.isArray(value)) {
            if (value.length === 0) {
                lines.push(`${prefix}${key}: []`);
            } else {
                lines.push(`${prefix}${key}:`);
                // gather list comments keyed as __#N.itemIndex
                const listComments = {};
                for (const k of Object.keys(obj)) {
                    const lm = k.match(/^__#\d+\.(\d+)$/);
                    if (lm) listComments[parseInt(lm[1])] = obj[k];
                }
                for (let i = 0; i < value.length; i++) {
                    if (listComments[i] !== undefined) {
                        for (const cl of listComments[i].split('\n'))
                            lines.push(`${prefix}${cl}`);
                    }
                    lines.push(`${prefix}- ${quoteIfNeeded(value[i])}`);
                }
            }
        } else if (value !== null && typeof value === "object") {
            lines.push(`${prefix}${key}:`);
            lines.push(format(value, indent + 1));
        } else if (typeof value === "string" && value.includes('\n')) {
            lines.push(`${prefix}${key}: |-`);
            for (const l of value.split('\n'))
                lines.push(`${prefix}  ${l}`);
        } else {
            lines.push(`${prefix}${key}: ${quoteIfNeeded(value) ?? ''}`);
        }
    }

    return lines.join('\n');
}

// ---------- CLI ----------

async function main() {
    let chunks = [];
    for await (const chunk of Deno.stdin.readable) chunks.push(chunk);
    const text = Buffer.concat(chunks).toString("utf8");
    const obj = parse(text);
    // console.log(obj);
    console.log(format(obj));
}

if (import.meta.main) main();
