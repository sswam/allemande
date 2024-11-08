#!/usr/bin/env python3-allemande

"""
This module calculates the median of numbers from stdin, line by line.
It skips any non-numbers encountered.
"""

import sys
import logging
from typing import TextIO
from statistics import median

from ally import main, logs, Get, Put

__version__ = "0.1.0"

logger = logs.get_logger()


def calculate_median(
    get: Get,
    put: Put,
) -> None:
    """
    Calculate the median of numbers from stdin, line by line.
    Skip any non-numbers encountered.
    """
    numbers = []

    while (line := get()) is not None:
        try:
            number = float(line.strip())
            numbers.append(number)
        except ValueError:
            logger.debug(f"Skipping non-number: {line.strip()}")
            continue

    if not numbers:
        logger.warning("No valid numbers found in input")
        return

    result = median(numbers)
    put(f"{result}")


def setup_args(arg):
    """Set up the command-line arguments."""
    # No additional arguments needed for this script


if __name__ == "__main__":
    main.go(calculate_median, setup_args)
