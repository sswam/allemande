#!/usr/bin/env python3-allemande

"""
This module reads text and indents content between specified brackets,
checking for mismatched brackets. It can process ( ) { } [ ] or < >,
with options to specify which brackets to process and how to format the output.
"""

import sys
import logging
from typing import TextIO, Callable

from ally import main, logs, Get, Put

__version__ = "0.1.0"

logger = logs.get_logger()


def brackets_indent(
    get: Get,
    put: Put,
    brackets: str = "(){}[]<>",
    join: bool = False,
    indent: str = "\t"
) -> None:
    """
    Read text, indent content within specified brackets,
    and check for mismatched brackets.
    """
    text = get(all=True)
    stack = []
    lines = text.splitlines()
    current_indent = 0
    error = 0

    for line in lines:
        new_line = ""
        i = 0
        while i < len(line):
            if line[i] in brackets:
                if line[i] in "({[<":
                    stack.append(line[i])
                    current_indent += 1
                    new_line += line[i]
                    if not join:
                        new_line += "\n" + indent * current_indent
                elif line[i] in ")}]>":
                    if not stack or brackets.index(stack.pop()) != brackets.index(line[i]) - 1:
                        logger.error(f"Mismatched bracket: {line[i]} at line: {line}")
                        error = 1
                    current_indent -= 1
                    if not join:
                        new_line += "\n" + indent * current_indent
                    new_line += line[i]
            else:
                new_line += line[i]
            i += 1

        put(indent * current_indent + new_line.strip())

    if stack:
        logger.error(f"Unclosed brackets: {', '.join(stack)}")
        error = 1

    return error


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-b", "--brackets", help="brackets to process")
    arg("-j", "--join", action="store_true", help="join content within brackets onto one line")
    arg("-I", "--indent", help="indentation string")


if __name__ == "__main__":
    main.go(setup_args, brackets_indent)

"""
FIXME: Improve handling of mixed bracket types within the same line.
"""
