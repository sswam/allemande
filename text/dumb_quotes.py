#!/usr/bin/env python3-allemande

"""
Convert smart quotes and similar typographic characters to their ASCII equivalents.
"""

import sys
import logging
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()

# Map of smart/fancy characters to their ASCII equivalents
REPLACEMENTS = {
    '\u201c': '"',  # U+201C LEFT DOUBLE QUOTATION MARK
    '\u201d': '"',  # U+201D RIGHT DOUBLE QUOTATION MARK
    '\u2018': "'",  # U+2018 LEFT SINGLE QUOTATION MARK
    '\u2019': "'",  # U+2019 RIGHT SINGLE QUOTATION MARK
    '\u2014': "-",  # U+2014 EM DASH
    '\u2013': "-",  # U+2013 EN DASH
    '…': "...",  # U+2026 HORIZONTAL ELLIPSIS
    '«': "<<",  # U+00AB LEFT-POINTING DOUBLE ANGLE QUOTATION MARK
    '»': ">>",  # U+00BB RIGHT-POINTING DOUBLE ANGLE QUOTATION MARK
}


def convert_quotes(istream: TextIO, ostream: TextIO) -> None:
    """Convert smart quotes and similar characters in input to ASCII equivalents."""
    for line in istream:
        for smart, plain in REPLACEMENTS.items():
            line = line.replace(smart, plain)
        ostream.write(line)


def setup_args(arg):
    """Set up command-line arguments."""
    # No arguments needed, we use stdin/stdout


if __name__ == "__main__":
    main.go(convert_quotes, setup_args)
