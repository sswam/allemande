#!/usr/bin/env python3

"""
This module checks if the input file is sorted, exiting with a warning if not.
"""

import sys
import logging

from ally import main, logs, geput  # type: ignore

__version__ = "0.1.1"

logger = logs.get_logger()


def check_sorted(
    get: geput.Get,
) -> None:
    """
    Check if the input file or stdin is sorted.
    Exit with code 1 and a warning if not sorted.
    """
    prev_line = None

    while True:
        line = get()
        if line is None:
            break

        if prev_line is not None and line < prev_line:
            logger.warning("Input is not sorted")
            sys.exit(1)

        prev_line = line

    logger.info("Input is sorted")


if __name__ == "__main__":
    main.go(check_sorted)
