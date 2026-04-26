'use strict';

// ym.js - "minus minus" YAML-like parser and formatter
// Usage (CLI): node ym.js < input.yaml

// ---------- helpers ----------

function getIndent(line) {
    return line.match(/^(\s*)/)[1].length;
}

function looksLikeKey(trimmed) {
    return /^\w[\w ./-]*\s*:/.test(trimmed);
}

function stripQuotes(s) {
    if (s && (s[0] === '"' || s[0] === "'"))
        return s.replace(/^["']|["']$/g, '').replace(/\\/g, '');
    return s;
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
        } else if (indent === 0 && !looksLikeKey(trimmed)) {
            // fault-tolerant: unindented non-key line included in value
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
    // collect implicit continuation lines after a string value
    const parts = [firstLine];
    while (idx < lines.length) {
        const line = lines[idx];
        const trimmed = line.trim();
        if (!trimmed) break;
        const indent = getIndent(line);
        if (indent > baseIndent) {
            parts.push(trimmed);
            idx++;
        } else if (indent === 0 && !looksLikeKey(trimmed)) {
            // fault-tolerant: unindented non-key line
            parts.push(trimmed);
            idx++;
        } else {
            break;
        }
    }
    return [parts.join('\n'), idx];
}

function parseEmptyValue(lines, idx, baseIndent) {
    // skip blank lines
    while (idx < lines.length && !lines[idx].trim()) idx++;

    if (idx >= lines.length) return ['', idx];

    const nextLine = lines[idx];
    const nextTrimmed = nextLine.trim();
    const nextIndent = getIndent(nextLine);

    if (nextIndent <= baseIndent) return ['', idx];

    if (nextTrimmed.startsWith('- ') || nextTrimmed === '-') {
        // array value
        const items = [];
        const arrIndent = nextIndent;
        while (idx < lines.length) {
            const line = lines[idx];
            const trimmed = line.trim();
            if (!trimmed) { idx++; continue; }
            const indent = getIndent(line);
            if (indent < arrIndent) break;
            if (indent > arrIndent) { idx++; continue; }
            if (!trimmed.startsWith('- ') && trimmed !== '-') break;
            items.push(trimmed.slice(2).trim());
            idx++;
        }
        return [items, idx];
    }

    // nested dict
    return parseBlock(lines, idx, nextIndent);
}

// ---------- main parser ----------

function parseBlock(lines, idx, baseIndent) {
    const obj = {};
    const order = [];
    let commentCount = 0;

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
            const ck = '__#' + commentCount++;
            obj[ck] = commentLines.join('\n');
            order.push(ck);
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
            [value, idx] = parseEmptyValue(lines, idx, baseIndent);
        } else {
            value = stripQuotes(value);
            [value, idx] = parseContinuation(lines, idx, baseIndent, value);
        }

        obj[key] = value;
        order.push(key);
    }

    obj.__order = order;
    return [obj, idx];
}

function parse(text) {
    const lines = text.split('\n');
    const [obj] = parseBlock(lines, 0, 0);
    return obj;
}

// ---------- formatter ----------

function format(obj, indent = 0) {
    const prefix = '  '.repeat(indent);
    const order = obj.__order
        || Object.keys(obj).filter(k => !k.startsWith('__'));
    const lines = [];

    for (const key of order) {
        if (key.startsWith('__#')) {
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
                for (const item of value)
                    lines.push(`${prefix}- ${item}`);
            }
        } else if (value !== null && typeof value === 'object') {
            lines.push(`${prefix}${key}:`);
            lines.push(format(value, indent + 1));
        } else if (typeof value === 'string' && value.includes('\n')) {
            lines.push(`${prefix}${key}: |-`);
            for (const l of value.split('\n'))
                lines.push(`${prefix}  ${l}`);
        } else {
            lines.push(`${prefix}${key}: ${value ?? ''}`);
        }
    }

    return lines.join('\n');
}

// ---------- CLI ----------

async function main() {
    const chunks = [];
    for await (const chunk of process.stdin) chunks.push(chunk);
    const text = Buffer.concat(chunks).toString('utf8');
    console.log(format(parse(text)));
}

// ---------- exports / entry ----------

if (typeof module !== 'undefined') module.exports = { parse, format };
if (typeof window !== 'undefined') window.ym = { parse, format };
if (typeof require !== 'undefined' && require.main === module) main();
