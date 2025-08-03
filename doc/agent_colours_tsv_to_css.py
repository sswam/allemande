#!/usr/bin/env python3-allemande

"""
Converts a CSV file containing user colors to CSS rules for light and dark modes.
"""

import sys
import logging
import csv
from typing import TextIO

from ally import main, logs  # type: ignore

logger = logs.get_logger()


def csv_to_css(istream: TextIO, ostream: TextIO) -> None:
    """Convert TSV color data to CSS rules for light and dark modes."""
    reader = csv.reader(istream, delimiter='\t')

    for row in reader:
        if not row or row[0].startswith('#'):
            continue

        if len(row) != 3:
            logger.warning("Skipping invalid row: %s", row)
            continue

        name, light_color, dark_color = row

        css = f""".message[user="{name}"] .label {{ color: {light_color}; }}; body.dark .message[user="{name}"] .label {{ color: {dark_color}; }}"""
        print(css, file=ostream)


def setup_args(arg):
    """Set up command-line arguments."""
    pass  # No arguments needed, using stdin/stdout


if __name__ == "__main__":
    main.go(csv_to_css, setup_args)
