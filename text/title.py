#!/usr/bin/env python3-allemande

"""
Convert input lines to title case, with optional smarts.
"""

import sys
import logging
from typing import TextIO, Callable
import re

from ally import main, logs, geput  # type: ignore
import titlecase  # type: ignore

__version__ = "0.1.1"

logger = logs.get_logger()


def process_line(line: str, simple: bool = False) -> str:
    """Convert a line to title case."""
    if not line.strip():
        return line

    if simple:
        return re.sub(r"\S+", lambda m: m.group().capitalize(), line)

    return titlecase.titlecase(line)


def title(
    get: geput.Get,
    put: geput.Put,
    simple: bool = False,
) -> None:
    """Convert input lines to title case."""
    print = geput.print(put)
    input = geput.input(get)

    while (line := input()) is not None:
        print(process_line(line, simple))


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-s", "--simple", action="store_true",
        help="simple mode: just capitalize first letter of each word")


if __name__ == "__main__":
    main.go(title, setup_args)
