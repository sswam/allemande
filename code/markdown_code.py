#!/usr/bin/env python

"""
This program extracts code blocks from Markdown text files. It can optionally
comment out non-code sections based on a provided comment prefix.
The extracted code along with commented non-code sections is then printed.

Dependencies:
- argh: Used for creating the command-line interface.

CLI Usage:
1.  Provide a Markdown file as input.
    markdown_code.py < file.md
2.  Optionally, specify a comment prefix to comment out non-code sections.
    markdown_code.py --comment-prefix="#"

The script handles:
- Code blocks enclosed in triple backticks (```) in the Markdown.
- Commenting out text that is not part of the code block when a comment prefix is provided.
"""

import sys
import re
import fileinput

import argh


def code_lines_to_string(lines):
    """
    Convert a list of code lines to a single string, ensuring trailing newlines are handled properly.

    Args:
        lines (list of str): A list of code lines.

    Returns:
        str: A single string representing the joined code lines.
    """

    stripped = [line.rstrip() for line in lines]

    while stripped and stripped[-1] == '':
        stripped.pop()

    if not stripped:
        return ''

    return '\n'.join(stripped + [''])


def extract_code_from_markdown(markdown_text, comment_prefix=None):
    """
    Finds and returns all code blocks within the given Markdown text,
    optionally commenting out non-code sections.

    Args:
        markdown_text (str): The input Markdown text.
        comment_prefix (str, optional): The prefix to use for commenting out non-code sections.
                                        If not provided, non-code sections are not included.

    Returns:
        str: The processed text with code blocks and commented non-code sections.
             Code blocks are returned as original, while non-code sections are optionally commented out.
    """

    # Pattern to capture code blocks starting with ```
    code_block_pattern = r'^```(?:\w*\n)?(.*?)^```'
    code_blocks = re.findall(code_block_pattern, markdown_text, re.DOTALL | re.MULTILINE)
    output = []
    last_index = 0

    # Find all code blocks with their starting positions.
    for match in re.finditer(code_block_pattern, markdown_text, re.DOTALL | re.MULTILINE):
        full_block = match.group(0)
        code = match.group(1).rstrip()
        start_index = match.start()
        non_code = markdown_text[last_index:start_index].strip()

        if non_code and comment_prefix is not None:
            output.extend([f"{comment_prefix} {line}" for line in non_code.split('\n')])
            output.append('')

        output.append(code)
        output.append('')

        last_index = match.end()

    remaining_text = markdown_text[last_index:].strip()
    if remaining_text and comment_prefix is not None:
        output.extend([f"{comment_prefix} {line}" for line in remaining_text.split('\n')])
        output.append('')

    return code_lines_to_string(output)


def main(comment_prefix=None):
    """
    Main function to extract code from Markdown text.

    Args:
        comment_prefix (str, optional): Prefix to add to each extracted code line as a comment. Defaults to None.
    """
    try:
        markdown_text = ''.join(fileinput.input()).strip()
        result = extract_code_from_markdown(markdown_text, comment_prefix=comment_prefix)
        print(result)
    except Exception as e:
        print(e, file=sys.stderr)


if __name__ == "__main__":
    # Dispatch the main function as an argh command-line interface
    argh.dispatch_command(main)
