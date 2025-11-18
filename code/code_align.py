#!/usr/bin/env python3-allemande

"""
Align blocks of end-of-line comments that appear after code on a line.
There should be 2 spaces or more between code and same-line comments.
"""

import re
from typing import TextIO

from ally import main  # type: ignore

__version__ = "0.1.9"


def detect_language(lines: list[str]) -> str:
    """Detect the programming language from initial lines."""
    # Check shebang
    if lines and lines[0].startswith("#!"):
        if "python" in lines[0].lower():
            return "python"
        return "shell"

    # Check first 10 lines for Python patterns
    check_lines = lines[:10]
    for line in check_lines:
        stripped = line.strip()
        if stripped.startswith(("import ", "from ", "def ", "class ")):
            return "python"
        if stripped.startswith(('"""', "'''")):
            return "python"

    # Default to generic (supports both # and //)
    return "generic"


def get_comment_pattern(language: str) -> str:
    """Get regex pattern for end-of-line comments based on language."""
    if language == "python":
        return r"(\s+)(#.*)$"
    if language == "shell":
        return r"(\s+)(#.*)$"
    # Generic: support both # and //
    return r"(\s+)((?:#|//).*)$"


def expand_tabs(line: str, tabstop: int) -> str:
    """Expand tabs to spaces."""
    result: list[str] = []
    col = 0
    for char in line:
        if char == "\t":
            spaces = tabstop - (col % tabstop)
            result.append(" " * spaces)
            col += spaces
        else:
            result.append(char)
            col += 1
    return "".join(result)


def parse_line_with_comment(line: str, pattern: re.Pattern) -> tuple[str, str, str] | None:
    """Parse a line into code, whitespace, and comment parts."""
    match = pattern.search(line)
    if not match:
        return None

    code = line[: match.start()]
    whitespace = match.group(1)
    comment = match.group(2)

    # Only process if there's code before the comment
    if code.strip():
        return (code, whitespace, comment)

    return None


def parse_line_with_equals(line: str) -> tuple[str, str, str] | None:
    """Parse a line into parts before equals, equals sign, and after."""
    # Match = or := that's not inside strings or comments
    # Simple approach: find first = or := before any # or //
    comment_pos = len(line)
    for marker in ("#", "//"):
        pos = line.find(marker)
        if pos != -1:
            comment_pos = min(comment_pos, pos)

    code_part = line[:comment_pos]

    op, op_len = None, 0
    # Look for := first, then =
    if ":=" in code_part:
        op, op_len = ":=", 2
    elif "=" in code_part:
        op, op_len = "=", 1

    if op:
        pos = code_part.find(op)
        before = code_part[:pos].rstrip()
        after = code_part[pos + op_len :].lstrip() + line[comment_pos:]
        if before:
            return (before, op, after)
    return None


def align_block(block: list[tuple[tuple, tuple]], block_lines: list[str], spacing: int = 2) -> list[str]:
    """Align comments or equals signs in a block of lines."""
    if not block:
        return block_lines

    parsed_expanded_list = [item[0] for item in block]

    code_lengths = [len(code.rstrip()) for code, _, _ in parsed_expanded_list]
    sorted_lengths = sorted(code_lengths)
    median = sorted_lengths[len(sorted_lengths) // 2] if code_lengths else 0
    threshold = median * 1.5 + 10
    normal_lengths = [length for length in code_lengths if length <= threshold]
    align_pos = max(normal_lengths) if normal_lengths else max(code_lengths) if code_lengths else 0

    result = []
    block_idx = 0

    for line in block_lines:
        if block_idx < len(block):
            parsed_expanded, parsed_original = block[block_idx]

            before_expanded, _, after_expanded = parsed_expanded
            before_original, separator_original, after_original = parsed_original

            before_len = len(before_expanded.rstrip())

            # Preserve the original line ending
            line_ending = ""
            if line.endswith("\n"):
                line_ending = "\n"
            after_original = after_original.rstrip("\r\n")

            # Check if this is an outlier
            is_outlier = len(block) > 2 and before_len > threshold

            if is_outlier:
                # Outlier: just add spacing
                spaces_needed = spacing
            else:
                # Normal: align to calculated position
                spaces_needed = align_pos - before_len + spacing

            # Format based on separator type (comment vs equals)
            is_comment_align = after_expanded.strip().startswith(('#', '//'))

            if is_comment_align:
                result.append(f"{before_expanded.rstrip()}{' ' * spaces_needed}{after_original}{line_ending}")
            else:
                result.append(f"{before_expanded.rstrip()}{' ' * spaces_needed}{separator_original} {after_original}{line_ending}")

            block_idx += 1
        else:
            result.append(line)

    return result


def align_equals(
    istream: TextIO,
    ostream: TextIO,
    tabstop: int = 0,
) -> None:
    """Align equals signs (or :=) in code blocks."""
    # Read initial lines for language detection
    initial_lines = []
    for _ in range(10):
        line = istream.readline()
        if not line:
            break
        initial_lines.append(line)

    # Detect language and set tabstop default
    language = detect_language(initial_lines)
    if tabstop == 0:
        tabstop = 4 if language == "python" else 8

    block: list[tuple[tuple, tuple]] = []
    block_lines: list[str] = []

    def flush_block() -> None:
        """Flush the current block."""
        nonlocal block, block_lines
        if block:
            aligned = align_block(block, block_lines, spacing=1
            for aligned_line in aligned:
                ostream.write(aligned_line)
            block = []
            block_lines = []

    def process_line(line: str) -> None:
        """Process a single line."""
        nonlocal block, block_lines

        # Expand tabs for width calculation
        expanded_line = expand_tabs(line, tabstop)

        # Check if line has an equals sign
        parsed_expanded = parse_line_with_equals(expanded_line.rstrip("\r\n"))
        parsed_original = parse_line_with_equals(line.rstrip("\r\n"))

        if parsed_expanded and parsed_original:
            # Line has equals, add to block
            block.append((parsed_expanded, parsed_original))
            block_lines.append(line)
        else:
            # No equals, flush block if any
            flush_block()
            # Output current line as-is
            ostream.write(line)

    # Process initial lines
    for line in initial_lines:
        process_line(line)

    # Process rest of input
    for line in istream:
        process_line(line)

    # Flush any remaining block
    flush_block()


def comments_align(
    istream: TextIO,
    ostream: TextIO,
    tabstop: int = 0,
) -> None:
    """Align blocks of end-of-line comments."""
    # Read initial lines for language detection
    initial_lines = []
    for _ in range(10):
        line = istream.readline()
        if not line:
            break
        initial_lines.append(line)

    # Detect language and set tabstop default
    language = detect_language(initial_lines)
    if tabstop == 0:
        tabstop = 4 if language == "python" else 8

    pattern = re.compile(get_comment_pattern(language))

    # Process initial lines and rest of input
    block: list[tuple[tuple, tuple]] = []
    block_lines: list[str] = []

    def process_line(line: str) -> None:
        """Process a single line."""
        nonlocal block, block_lines

        # Expand tabs for width calculation
        expanded_line = expand_tabs(line, tabstop)

        # Check if line has a trailing comment, on both original and expanded
        parsed_expanded = parse_line_with_comment(expanded_line, pattern)
        parsed_original = parse_line_with_comment(line, pattern)

        if parsed_expanded and parsed_original:
            # Line has comment after code, add to block
            block.append((parsed_expanded, parsed_original))
            block_lines.append(line)
        else:
            # No trailing comment, flush block if any
            if block:
                aligned = align_block(block, block_lines)
                for aligned_line in aligned:
                    ostream.write(aligned_line)
                block = []
                block_lines = []

            # Output current line as-is
            ostream.write(line)

    # Process initial lines
    for line in initial_lines:
        process_line(line)

    # Process rest of input
    for line in istream:
        process_line(line)

    # Flush any remaining block
    if block:
        aligned = align_block(block, block_lines)
        for aligned_line in aligned:
            ostream.write(aligned_line)


def code_align(
    istream: TextIO,
    ostream: TextIO,
    tabstop: int = 0,
    comments: bool = True,
    equals: bool = False,
) -> None:
    """Align code based on options."""
    import io

    # If aligning equals, do that first
    if equals:
        temp_stream = io.StringIO()
        align_equals(istream, temp_stream, tabstop)
        temp_stream.seek(0)

        # If also aligning comments, use temp as input
        if comments:
            comments_align(temp_stream, ostream, tabstop)
        else:
            ostream.write(temp_stream.getvalue())
    elif comments:
        comments_align(istream, ostream, tabstop)
    else:
        # No alignment requested, just copy
        for line in istream:
            ostream.write(line)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-t", "--tabstop", help="tab width (default: 4 for Python, 8 for others)")
    arg("-c", "--comments", help="align comments (default: true)")
    arg("-e", "--equals", help="align equals signs or := (default: false)")


if __name__ == "__main__":
    main.go(code_align, setup_args)


# Issues:
# 1. In `align_block`, when outputting aligned lines,
# `before_expanded.rstrip()` is used for the code part,
# which expands indentation tabs to spaces, but the added test
# `test_comments_align_preserves_indentation_tabs` expects indentation tabs to
# be preserved as-is in the output. This causes the test to fail with expanded
# spaces instead of original tabs. To fix, consider separating indentation from
# code in parsing or adjusting output logic to use original indentation with
# expanded alignment.
