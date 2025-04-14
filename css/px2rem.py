#!/usr/bin/env python3-allemande

"""
Convert pixel values to rem units in CSS, dividing by 16 and handling zero values.
"""

import sys
import re
import logging
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


def px_to_rem(match: re.Match) -> str:
    """Convert a pixel value to rem, handling zero specially."""
    px_val = match.group(1)
    if px_val == "0":
        return "0"
    return f"{float(px_val) / 16}rem"


def convert_line(line: str) -> str:
    """Convert all pixel values in a line to rem units."""
    return re.sub(r"(\d+)px\b", px_to_rem, line)


def process_css(istream: TextIO, ostream: TextIO) -> None:
    """Process CSS input, converting px to rem values."""
    for line in istream:
        logger.debug("Processing line: %s", line.rstrip())
        converted = convert_line(line)
        ostream.write(converted)


def setup_args(arg):
    """Set up command-line arguments."""
    # No additional arguments needed for basic functionality


if __name__ == "__main__":
    main.go(process_css, setup_args)
