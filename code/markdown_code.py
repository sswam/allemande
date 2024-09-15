#!/usr/bin/env python

"""
This program extracts code blocks from Markdown text files. It can optionally
comment out non-code sections based on a provided comment prefix.
The extracted code along with commented non-code sections is then printed.

Features:
- Extracts code blocks enclosed in triple backticks (```) from Markdown.
- Optionally comments out non-code sections with a specified prefix.
- Can select specific code blocks to extract.
- Outputs plain text as-is if no code blocks are found.
- Implements shebang fix: moves #! line to the top if found in the first 3 lines.

Dependencies:
- argh: Used for creating the command-line interface.

CLI Usage:
1. Provide a Markdown file as input:
   markdown_code.py < file.md

2. Optionally, specify a comment prefix to comment out non-code sections:
   markdown_code.py --comment-prefix="#"

3. Optionally, select specific code blocks to extract:
   markdown_code.py 0 2  # Extracts the first and third code blocks

4. Disable plain text output when no code blocks are found:
   markdown_code.py --no-plain-text

5. Enable shebang fix:
   markdown_code.py --shebang-fix
"""

import sys
import re

import argh
from argh import arg


def code_lines_to_string(lines, strip):
    """
    Convert a list of code lines to a single string, ensuring trailing newlines are handled properly.

    Args:
        lines (list of str): A list of code lines.

    Returns:
        str: A single string representing the joined code lines.
    """
    if strip:
        lines = [line.rstrip() for line in lines]

        while lines and lines[-1] == '':
            lines.pop()

    if not lines:
        return ''

    return '\n'.join(lines + [''])


@arg('--no-shebang-fix', dest='shebang_fix', action='store_false')
@arg('--no-strip', dest='strip', action='store_false')
def extract_code_from_markdown(*select, istream=sys.stdin, comment_prefix=None, strict_code=False, shebang_fix=True, strip=True):
    """
    Finds and returns all code blocks within the given Markdown text,
    optionally commenting out non-code sections and applying shebang fix.

    Args:
        istream: The input stream of markdown text, or it can be a string.
        *select Variable number of int: Indices of code blocks to extract. If none, all blocks are extracted.
        comment_prefix (str, optional): Prefix to add to each extracted code line as a comment. Defaults to None.
        strict_code (bool): If False, output the original markdown when no code blocks are found.
        shebang_fix (bool): If True, move shebang line to the top if found in the first 3 lines.
        strip (bool): If True, strip whitespace from end of lines and end of file (leaving one newline before EOF).

    Returns:
        str: The processed text with code blocks and commented non-code sections.
             Code blocks are returned as original, while non-code sections are optionally commented out.
    """

    if isinstance(istream, str):
        markdown_text = istream
    else:
        markdown_text = sys.stdin.read().strip()

    select = [int(s) for s in select] or None

    code_block_pattern = r'^```(?:\w*\n)?(.*?)^```'
    output = []
    last_index = 0
    count = 0
    code_blocks_found = False
    shebang_line = None

    for match in re.finditer(code_block_pattern, markdown_text, re.DOTALL | re.MULTILINE):
        code_blocks_found = True
        full_block = match.group(0)
        code = match.group(1).rstrip()
        start_index = match.start()
        non_code = markdown_text[last_index:start_index].strip()

        if non_code and comment_prefix is not None:
            output.extend([f"{comment_prefix} {line}" for line in non_code.split('\n')])
            output.append('')

        if select is None or count in select:
            if shebang_fix and count == 0:
                code_lines = code.split('\n')
                for i, line in enumerate(code_lines[:3]):
                    if line.startswith('#!'):
                        shebang_line = line
                        code_lines.pop(i)
                        break
                code = '\n'.join(code_lines)
            output.append(code)
            output.append('')

        last_index = match.end()
        count += 1

    if not code_blocks_found and strict_code:
        return markdown_text.strip()

    remaining_text = markdown_text[last_index:].strip()
    if remaining_text and comment_prefix is not None:
        output.extend([f"{comment_prefix} {line}" for line in remaining_text.split('\n')])
        output.append('')

    lines = [line for block in output for line in block.split('\n')]

    if shebang_line:
        lines.insert(0, shebang_line)

    return code_lines_to_string(lines, strip)


if __name__ == "__main__":
    argh.dispatch_command(extract_code_from_markdown, raw_output=True)
