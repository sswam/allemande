#!/usr/bin/env python

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

Dependencies:
- argh: Used for creating the command-line interface.

CLI Usage:
1.  Provide a Markdown file as input:
    markdown_code.py < file.md

2.  Optionally, specify comment prefixes to comment out non-code sections:
    markdown_code.py --start-comment="/*" --end-comment="*/"

3.  Optionally, select specific code blocks to extract:
    markdown_code.py 0 2  # Extracts the first and third code blocks

4.  Disable plain text output when no code blocks are found:
    markdown_code.py --no-plain-text

5.  Enable shebang fix:
    markdown_code.py --shebang-fix
"""

import sys
import re
from typing import List, Optional, Tuple

import argh
from argh import arg

__version__ = "1.0.1"  # Bumped patch version

CODE_BLOCK_PATTERN = r"^```(?:\w*\n)?(.*?)^```"


def code_lines_to_string(lines: List[str], strip: bool) -> str:
    """
    Convert a list of code lines to a single string, ensuring trailing newlines are handled properly.

    Args:
        lines (List[str]): A list of code lines.
        strip (bool): If True, strip whitespace from end of lines and end of file.

    Returns:
        str: A single string representing the joined code lines.
    """
    if strip:
        lines = [line.rstrip() for line in lines]
        while lines and lines[-1] == "":
            lines.pop()

    if not lines:
        return ""

    return "\n".join(lines + [""])


def unicde_escape(text: str) -> str:
    """ Escape all characters in the given text using unicode escapes. """
    return "".join(f"\\u{ord(c):04x}" for c in text)

def comment_text(text: str, start_comment: str, end_comment: str) -> List[str]:
    """
    Comment out the given text with the specified start and end comments.

    Args:
        text (str): The text to comment out.
        start_comment (str): The prefix to use for starting a comment.
        end_comment (str): The suffix to use for ending a comment.

    Returns:
        List[str]: A list of commented lines.
    """
    start_comment = start_comment + " " if start_comment else ""
    end_comment = " " + end_comment if end_comment else ""

    lines = text.split("\n")
    commented_lines = [f"{start_comment} {line}" for line in lines]

    # Get rid of end_comment if it appears within the commented text
    for i, line in enumerate(commented_lines):
        while end_comment and end_comment in line:
            commented_lines[i] = line.replace(end_comment, unicde_escape(end_comment))

    if len(commented_lines) <= 1 or not end_comment:
        return [f"{start_comment}{text}{end_comment}" for text in lines]

    # in this way we don't change the line numbering FWIW
    return [f"{start_comment}{lines[0]}"] + lines[1:-1] + [f"{lines[-1]}{end_comment}"]


def handle_shebang(code: str) -> Tuple[str, Optional[str]]:
    """
    Extract the shebang line from the code if present in the first 3 lines.

    Args:
        code (str): The code to process.

    Returns:
        Tuple[str, Optional[str]]: The code without the shebang and the shebang line if found.
    """
    code_lines = code.split("\n")
    shebang_line = None
    for i, line in enumerate(code_lines[:3]):
        if line.startswith("#!"):
            shebang_line = line
            code_lines.pop(i)
            break
    return "\n".join(code_lines), shebang_line


@arg("--no-shebang-fix", dest="shebang_fix", action="store_false")
@arg("--no-strip", dest="strip", action="store_false")
@arg("--no-first", dest="first", action="store_false")
@arg("--start-comment", "-c", default=None)
@arg("--end-comment", "-e", default=None)
def extract_code_from_markdown(
    *select,
    input_source=sys.stdin,
    start_comment: Optional[str] = None,
    end_comment: Optional[str] = None,
    strict_code: bool = False,
    shebang_fix: bool = True,
    strip: bool = True,
    first: bool = True,
) -> str:
    """
    Finds and returns all code blocks within the given Markdown text,
    optionally commenting out non-code sections and applying shebang fix.

    Args:
        input_source: The input stream of markdown text, or it can be a string.
        *select: Variable number of int: Indices of code blocks to extract. If none, all blocks are extracted.
        start_comment (str, optional): Prefix to start a comment. Defaults to None.
        end_comment (str, optional): Suffix to end a comment, if applicable. Defaults to None.
        strict_code (bool): If False, output the original markdown when no code blocks are found.
        shebang_fix (bool): If True, move shebang line to the top if found in the first 3 lines.
        strip (bool): If True, strip whitespace from end of lines and end of file (leaving one newline before EOF).
        keep (bool): Use with select. If True, output the selected blocks first, and keep the rest as comments.

    Returns:
        str: The processed text with code blocks and commented non-code sections.
    """
    try:
        if isinstance(input_source, str):
            markdown_text = input_source
        else:
            markdown_text = input_source.read().strip()
    except Exception as e:
        print(f"Error reading input: {e}", file=sys.stderr)
        return ""

    select = [int(s) for s in select] or None

    if first and not select:
        select = [0]

    # be clever with block comments
    if end_comment is None:
        if start_comment == "/*":
            end_comment = "*/"
        elif start_comment == "<!--":
            end_comment = "-->"

    output = []
    last_index = 0
    count = 0
    code_blocks_found = False
    shebang_line = None
    kept_blocks = []

    def process_text(text):
        if first:
            kept_blocks.append(text)
        elif start_comment is not None:
            output.extend(comment_text(text, start_comment, end_comment))
            output.append("")

    def process_code(code):
        output.append(code)
        output.append("")

    for match in re.finditer(
        CODE_BLOCK_PATTERN, markdown_text, re.DOTALL | re.MULTILINE
    ):
        code_blocks_found = True
        code = match.group(1).rstrip()
        start_index = match.start()
        text = markdown_text[last_index:start_index].strip()

        if text and start_comment is not None:
            process_text(text)

        if shebang_fix and count == 0 and not shebang_line:
            code, shebang_line = handle_shebang(code)

        if select is None or count in select:
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


if __name__ == "__main__":
    argh.dispatch_command(extract_code_from_markdown, raw_output=True)
