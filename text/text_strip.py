#!/usr/bin/env python3-allemande

"""
Clean up text by removing trailing whitespace from lines and blank lines from the top.
"""

import sys
from typing import TextIO
from ally import main, logs, geput  # type: ignore

__version__ = "0.1.2"

logger = logs.get_logger()


def text_strip(get: geput.Get, put: geput.Put) -> None:
    """
    Clean text by removing leading and trailing blank lines,
    and trailing whitespace from each line.
    """
    input = geput.input(get)
    print = geput.print(put)

    first_line = True
    found_content = False

    blank_count = 0

    while (line := input()) is not None:
        line = line.rstrip()

        # remove UTF-8 BOM from first line
        if first_line:
            line = line.lstrip("\ufeff")
            first_line = False

        if not found_content and not line:
            continue

        if not line:
            blank_count += 1
            continue

        found_content = True

        for _ in range(blank_count):
            print("")
        blank_count = 0

        print(line)


if __name__ == "__main__":
    main.go(text_strip)
