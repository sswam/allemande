#!/usr/bin/env python3

"""
This module adjusts hex colors in input text by a specified factor.
"""

import sys
import re
import logging
from typing import TextIO

from argh import arg

from ally import main

__version__ = "0.1.0"

logger = main.get_logger()


def adjust_hex_color(hex_color: str, factor: float) -> str:
    """Adjust a hex color by the given factor."""
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    r = min(255, max(0, int(r * factor)))
    g = min(255, max(0, int(g * factor)))
    b = min(255, max(0, int(b * factor)))
    return f"#{r:02x}{g:02x}{b:02x}"


def process_line(line: str, factor: float) -> str:
    """Process a single line of input, adjusting hex colors."""
    def replace_color(match):
        return adjust_hex_color(match.group(0), factor)

    return re.sub(r'#[0-9A-Fa-f]{6}', replace_color, line)


@arg("--factor", "-f", help="factor to adjust colors by", type=float, default=0.5)
def hex_adjust(
    factor: float = 0.5,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Adjust hex colors in input text by a specified factor.
    """
    get, put = main.io(istream, ostream)

    if factor <= 0:
        logger.warning("Factor should be positive. Using absolute value.")
        factor = abs(factor)

    while (line := get()) is not None:
        adjusted_line = process_line(line, factor)
        put(adjusted_line)


if __name__ == "__main__":
    main.run(hex_adjust)
