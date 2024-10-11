#!/usr/bin/env python3

"""
This program extracts code blocks from Markdown text files. It can optionally
comment out non-code sections based on provided comment prefixes.
The extracted code along with commented non-code sections is then printed.

Features:
  - Extracts code blocks enclosed in triple backticks (```) from Markdown.
  - Optionally comments out non-code sections with specified start and end comments.
  - Can select specific code blocks to extract.
  - Outputs plain text as-is if no code blocks are found.
  - Implements shebang fix: moves #! line to the top if found in the first 3 lines.
"""

import sys
import re
import logging
from typing import TextIO
import argparse

from ally import main

__version__ = "1.0.4"

logger = main.get_logger()

CODE_BLOCK_PATTERN = r"^```(?:\w*\n)?(.*?)^```"


def code_lines_to_string(lines: list[str], strip: bool) -> str:
    """
    Convert a list of code lines to a single string, ensuring trailing newlines are handled properly.
    """
    if strip:
        lines = [line.rstrip() for line in lines]
        while lines and lines[-1] == "":
            lines.pop()

    if not lines:
        return ""

    return "\n".join(lines + [""])


def unicode_escape(text: str) -> str:
    """Escape all characters in the given text using unicode escapes."""
    return "".join(f"\\u{ord(c):04x}" for c in text)


def comment_text(text: str, start_comment: str, end_comment: str) -> list[str]:
    """Comment out the given text with the specified start and end comments."""
    start_comment = start_comment + " " if start_comment else ""
    end_comment = " " + end_comment if end_comment else ""

    lines = text.split("\n")
    commented_lines = [f"{start_comment} {line}" for line in lines]

    # Get rid of end_comment if it appears within the commented text
    for i, line in enumerate(commented_lines):
        while end_comment and end_comment in line:
            commented_lines[i] = line.replace(end_comment, unicode_escape(end_comment))

    if len(commented_lines) <= 1 or not end_comment:
        return [f"{start_comment}{text}{end_comment}" for text in lines]

    # in this way we don't change the line numbering FWIW
    return [f"{start_comment}{lines[0]}"] + lines[1:-1] + [f"{lines[-1]}{end_comment}"]


def handle_shebang(code: str) -> tuple[str, str | None]:
    """Extract the shebang line from the code if present in the first 3 lines."""
    code_lines = code.split("\n")
    shebang_line = None
    for i, line in enumerate(code_lines[:3]):
        if line.startswith("#!"):
            shebang_line = line
            code_lines.pop(i)
            break
    return "\n".join(code_lines), shebang_line


def extract_code_from_markdown(
    *select: int,
    input_source: TextIO | str = sys.stdin,
    start_comment: str | None = None,
    end_comment: str | None = None,
    strict_code: bool = False,
    shebang_fix: bool = True,
    strip: bool = True,
    first: bool = True,
) -> str:
    """
    Finds and returns all code blocks within the given Markdown text,
    optionally commenting out non-code sections and applying shebang fix.
    """
    try:
        if isinstance(input_source, str):
            markdown_text = input_source
        else:
            markdown_text = input_source.read().strip()
    except Exception as e:
        logger.error(f"Error reading input: {e}")
        return ""

    select_list = list(select) or None

    if first and not select_list:
        select_list = [0]

    # be clever with block comments
    if end_comment is None:
        if start_comment == "/*":
            end_comment = "*/"
        elif start_comment == "<!--":
            end_comment = "-->"
        else:
            end_comment = ""

    output = []
    last_index = 0
    count = 0
    code_blocks_found = False
    shebang_line = None
    kept_blocks = []

    def process_text(text: str) -> None:
        if first:
            kept_blocks.append(text)
        elif start_comment is not None:
            output.extend(comment_text(text, start_comment, end_comment))
            output.append("")

    def process_code(code: str) -> None:
        output.append(code)
        output.append("")

    for match in re.finditer(CODE_BLOCK_PATTERN, markdown_text, re.DOTALL | re.MULTILINE):
        code_blocks_found = True
        code = match.group(1).rstrip()
        start_index = match.start()
        text = markdown_text[last_index:start_index].strip()

        if text and start_comment is not None:
            process_text(text)

        if shebang_fix and count == 0 and not shebang_line:
            code, shebang_line = handle_shebang(code)

        if select_list is None or count in select_list:
            process_code(code)
        elif first:
            kept_blocks.append(code)

        last_index = match.end()
        count += 1

    remaining_text = markdown_text[last_index:].strip()
    if remaining_text and start_comment is not None:
        process_text(remaining_text)

    if not code_blocks_found and strict_code:
        return markdown_text.strip()

    for block in kept_blocks:
        if start_comment is not None:
            output.extend(comment_text(block, start_comment, end_comment))
            output.append("")

    lines = [line for block in output for line in block.split("\n")]

    if shebang_line:
        lines.insert(0, shebang_line)
        if not (len(lines) > 1 and lines[1] == ""):
            lines.insert(1, "")

    return code_lines_to_string(lines, strip)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("select", nargs="*", type=int, help="Select specific code blocks to extract")
    arg("--start-comment", "-c", default=None, help="Comment prefix to add to non-code sections")
    arg("--end-comment", "-e", default=None, help="Comment suffix to add to non-code sections")
    arg("--no-shebang-fix", "-H", dest="shebang_fix", action="store_false", help="Shebang fix")
    arg("--no-strip", "-S", dest="strip", action="store_false", help="Strip trailing whitespace")
    arg("--no-first", "-F", dest="first", action="store_false", help="Extract first code block only")
    arg("--strict-code", "-s", action="store_true", help="Output plain text if no code blocks are found")

if __name__ == "__main__":
    main.go(setup_args, extract_code_from_markdown)
