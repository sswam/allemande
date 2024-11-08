#!/usr/bin/env python3-allemande

"""
This module adds column numbers to TSV files.
"""

import sys
import logging
from typing import TextIO, Callable

from ally import main, logs, geput

__version__ = "0.1.0"

logger = logs.get_logger()


def tsv_number_columns(
    get: geput.Get,
    put: geput.Put,
    start: int = 1,
) -> None:
    """
    Read a TSV file, add column numbers, and output the result.
    """
    # Read all lines from input
    lines = list(geput.each(get))
    print = geput.print(put)

    if not lines:
        logger.warning("Input is empty")
        return

    # Find the maximum number of columns
    max_columns = max(len(line.split('\t')) for line in lines)
    logger.info(f"Maximum number of columns: {max_columns}")

    # Generate the column numbers row
    numbers_row = '\t'.join(str(i) for i in range(start, start + max_columns))

    # Output the column numbers row
    print(numbers_row)

    # Output the rest of the file
    for line in lines:
        put(line)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-s", "--start", help="starting number for column numbering")


if __name__ == "__main__":
    main.go(tsv_number_columns, setup_args)
