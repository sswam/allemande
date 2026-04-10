#!/usr/bin/env python3

"""
code_header.py - Extract the header comment block from a source file.

Supports #-comments (Python, shell), //-comments, /* ... */ block comments,
and Python triple-quoted docstrings. Strips shebang and encoding declarations,
and removes a trailing comment group that appears to belong to the first
function/section rather than the file header.
"""

import argparse
import logging
import re
import sys

log = logging.getLogger(__name__)

_ENCODING_RE = re.compile(r"#.*coding[:=]")

# File extensions that use C-style comments
_C_STYLE_EXTS = {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".js", ".ts", ".java", ".cs", ".go", ".swift", ".kt", ".rs", ".m", ".mm"}

# Patterns that indicate C-style source even without extension match
_C_STYLE_RE = re.compile(r"^\s*(//|/\*|#include|#define|#if|#ifdef|#ifndef|#endif|#pragma)")


def _is_c_style_ext(path: str) -> bool:
    """Return True if the file extension indicates C-style comments."""
    import os
    _, ext = os.path.splitext(path)
    return ext.lower() in _C_STYLE_EXTS


def _collect_header_lines(lines: list[str], style: str | None = None) -> list[str]:
    """Collect leading blank and comment lines, stopping at the first code line.

    If style is None, auto-detect C-style from content.
    """
    collected = []
    in_block = False
    in_docstring = False
    ds_delim: str | None = None

    for line in lines:
        stripped = line.strip()

        # Auto-detect C-style on the fly
        if style is None and _C_STYLE_RE.match(line):
            style = "c"

        if in_block:
            collected.append(line)
            if "*/" in line:
                in_block = False
            continue

        if in_docstring:
            collected.append(line)
            assert ds_delim is not None
            if ds_delim in stripped:
                in_docstring = False
            continue

        if not stripped:
            collected.append(line)
        elif stripped.startswith("//") or stripped.startswith("/*"):
            collected.append(line)
            if stripped.startswith("/*") and stripped.find("*/", 2) == -1:
                in_block = True
        elif stripped.startswith("#") and style != "c":
            collected.append(line)
        elif stripped.startswith('"""') or stripped.startswith("'''"):
            ds_delim = stripped[:3]
            collected.append(line)
            if ds_delim not in stripped[3:]:
                in_docstring = True
        else:
            break

    return collected


def _strip_preamble(lines: list[str]) -> list[str]:
    """Remove shebang and encoding-declaration lines from the top."""
    result = list(lines)
    while result:
        s = result[0].strip()
        if s.startswith("#!") or _ENCODING_RE.search(s):
            result.pop(0)
        else:
            break
    return result


def _apply_heuristic(lines: list[str]) -> list[str]:
    """Remove a trailing comment block likely associated with the first function.

    Pattern: [header comments] [blank line] [comment block] (no trailing blank)
    → strip the blank and everything after it.
    """
    last_blank = None
    for i in range(len(lines) - 1, -1, -1):
        if not lines[i].strip():
            last_blank = i
            break

    if last_blank is None or last_blank == 0:
        return lines

    after_blank = lines[last_blank + 1:]
    if after_blank and all(line.strip() for line in after_blank):
        return lines[:last_blank]

    return lines


def _strip_comment_chars(text: str) -> str:
    """Strip comment characters from each line of a header block."""
    result = []
    in_block = False
    for line in text.splitlines():
        s = line.strip()
        if in_block:
            if s.endswith("*/"):
                s = s[:-2].strip()
            elif s.startswith("*"):
                s = s[1:].strip()
            if "*/" in line:
                in_block = False
        elif s.startswith("/*"):
            s = s[2:].strip()
            if s.endswith("*/"):
                s = s[:-2].strip()
            else:
                in_block = True
        elif s.startswith("//"):
            s = s[2:].strip()
        elif s.startswith("#"):
            s = s[1:].strip()
        elif s.startswith('"""') or s.startswith("'''"):
            delim = s[:3]
            s = s[3:]
            if s.endswith(delim):
                s = s[:-3]
            s = s.strip()
        result.append(s)
    return "\n".join(result)


def extract_header(source: str, style: str | None = None) -> str:
    """Extract the header comment block from source code string."""
    lines = source.splitlines()
    collected = _collect_header_lines(lines, style=style)
    collected = _strip_preamble(collected)
    collected = _apply_heuristic(collected)

    while collected and not collected[-1].strip():
        collected.pop()

    result = "\n".join(collected).strip()
    return result + "\n" if result else ""


def extract_file_header(path: str, style: str | None = None) -> str:
    """Load a source file and return its header comment block."""
    if style is None and _is_c_style_ext(path):
        style = "c"
    with open(path) as f:
        source = f.read()
    header = extract_header(source, style=style)
    if not header:
        log.debug("No header found in %s", path)
    return header


def main() -> None:
    logging.basicConfig(level=logging.WARNING)

    parser = argparse.ArgumentParser(description="Extract header comment block from a source file.")
    parser.add_argument("file", help="Source file to process")
    parser.add_argument("--strip", "-s", action="store_true", help="Strip comment characters from output")
    args = parser.parse_args()

    header = extract_file_header(args.file)
    if not header:
        sys.exit(1)

    if args.strip:
        header = _strip_comment_chars(header)
        # Remove leading/trailing blank lines after stripping
        header = header.strip() + "\n"

    print(header, end="")


if __name__ == "__main__":
    main()
