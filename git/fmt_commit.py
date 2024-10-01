#!/usr/bin/env python3

"""
This module formats git commit messages by adding two spaces before continued lines.
"""

import sys
import logging
from typing import TextIO

from argh import arg

from ally import main

__version__ = "0.1.0"

logger = main.get_logger()


def format_commit_message(lines: list[str]) -> list[str]:
    """Format the commit message by adding two spaces before continued lines."""
    formatted_lines = []
    for line in lines:
        if not line.startswith("- ") and formatted_lines and formatted_lines[-1].startswith("- "):
            line = "  " + line
        formatted_lines.append(line)
    return formatted_lines


def fmt_commit(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Format git commit messages by adding two spaces before continued lines.
    """
    get, put = main.io(istream, ostream)

    lines = get(lines=True)
    formatted_lines = format_commit_message(lines)
    put(formatted_lines, lines=True)


if __name__ == "__main__":
    main.run(fmt_commit)
