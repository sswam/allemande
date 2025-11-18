#!/usr/bin/env python3-allemande

"""
Align blocks of end-of-line comments that appear after code on a line.
"""

import re
from typing import TextIO

from ally import main  # type: ignore

__version__ = "0.1.5"


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


def calculate_alignment(block: list[tuple[str, str, str]]) -> int:
    """Calculate alignment position, excluding outliers."""
    if not block:
        return 0

    code_lengths = [len(code.rstrip()) for code, _, _ in block]

    # If only one or two lines, no outlier detection needed
    if len(code_lengths) <= 2:
        return max(code_lengths)

    # Calculate median to detect outliers
    sorted_lengths = sorted(code_lengths)
    median = sorted_lengths[len(sorted_lengths) // 2]

    # Filter out outliers (lines much longer than median)
    threshold = median * 1.5 + 10
    normal_lengths = [length for length in code_lengths if length <= threshold]

    if not normal_lengths:
        return max(code_lengths)

    return max(normal_lengths)


def align_block(block: list[tuple[str, str, str]], block_lines: list[str], spacing: int = 2) -> list[str]:
    """Align comments or equals signs in a block of lines."""
    if not block:
        return block_lines

    is_comment_align = not block[0][1].strip()

    if is_comment_align:
        align_pos = calculate_alignment(block)
        code_lengths = [len(code) for code, _, _ in block]
    else:  # equals align
        align_pos = calculate_alignment(block)
        code_lengths = [len(code) for code, _, _ in block]

    # Calculate median for outlier detection
    code_lengths = [len(code) for code, _, _ in block]
    sorted_lengths = sorted(code_lengths)
    median = sorted_lengths[len(sorted_lengths) // 2] if sorted_lengths else 0
    threshold = median * 1.5 + 10

    result = []
    block_idx = 0

    for line in block_lines:
        if block_idx < len(block):
            before, separator, after = block[block_idx]
            before_len = len(before.rstrip())

            # Preserve the original line ending
            line_ending = ""
            if line.endswith("\n"):
                line_ending = "\n"
            after = after.rstrip("\r\n")

            # Check if this is an outlier
            if len(block) > 2 and before_len > threshold:
                # Outlier: just add spacing
                if is_comment_align:
                    result.append(f"{before}{' ' * spacing}{after}{line_ending}")
                else:
                    result.append(f"{before} {separator} {after}{line_ending}")
            else:
                # Normal: align to calculated position
                spaces_needed = align_pos - before_len + spacing
                if is_comment_align:
                    result.append(f"{before}{' ' * spaces_needed}{after}{line_ending}")
                else:
                    result.append(f"{before}{' ' * spaces_needed}{separator} {after}{line_ending}")
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
    lines = istream.readlines()

    # Detect language and set tabstop default
    language = detect_language(lines)
    if tabstop == 0:
        tabstop = 4 if language == "python" else 8

    block = []
    block_lines = []

    def flush_block() -> None:
        """Flush the current block."""
        nonlocal block, block_lines
        if block:
            aligned = align_block(block, block_lines, spacing=1)
            for aligned_line in aligned:
                ostream.write(aligned_line)
            block = []
            block_lines = []

    for line in lines:
        # Expand tabs
        expanded_line_with_nl = expand_tabs(line, tabstop)

        # Check if line has an equals sign
        parsed = parse_line_with_equals(expanded_line_with_nl.rstrip("\r\n"))

        if parsed:
            # Line has equals, add to block
            block.append(parsed)
            block_lines.append(expanded_line_with_nl)
        else:
            # No equals, flush block if any
            flush_block()
            # Output current line as-is
            ostream.write(expanded_line_with_nl)

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
    block = []
    block_lines = []

    def process_line(line: str) -> None:
        """Process a single line."""
        nonlocal block, block_lines

        # Expand tabs
        line = expand_tabs(line, tabstop)

        # Check if line has a trailing comment
        parsed = parse_line_with_comment(line, pattern)

        if parsed:
            # Line has comment after code, add to block
            block.append(parsed)
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
# 1.  In `align_equals`, the entire input stream is read into memory with
# `istream.readlines()`. For consistency with `comments_align` which processes
# the input as a stream, you might consider refactoring `align_equals` to also
# stream its input after an initial lookahead for language detection. This
# would improve its memory usage and performance on very large files.
#
# 2.  The logic for detecting outliers appears to be duplicated. The
# threshold is calculated in `calculate_alignment` and then calculated again in
# `align_block`. This could be simplified by having `calculate_alignment` also
# return the threshold it used, or by checking for outliers in `align_block`
# more directly, for instance by treating any line where `len(before.rstrip())
# > align_pos` as an outlier.
