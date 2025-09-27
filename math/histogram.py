#!/usr/bin/env python3-allemande

"""
Create a histogram from numbers read from stdin.
"""

import sys
from typing import TextIO

import numpy as np

from ally import main, logs

__version__ = "0.1.0"

logger = logs.get_logger()


def read_numbers(istream: TextIO) -> list[float]:
    """Read numbers from input stream, one per line."""
    numbers = []
    for line in istream:
        try:
            num = float(line.strip())
            numbers.append(num)
        except ValueError:
            logger.warning("Skipping invalid number: %s", line.strip())
            continue
    return numbers


def histogram(
    istream: TextIO,
    ostream: TextIO,
    bins: int = 10,
    log: bool = False,
    log_values: bool = False,
    min: float | None = None,
    max: float | None = None,
) -> None:
    """Create a histogram from numbers in input stream."""
    range = (min, max) if min is not None and max is not None else None

    if log_values:
        log = True
    numbers = read_numbers(istream)
    if not numbers:
        raise ValueError("No valid numbers found in input")

    if log:
        numbers = np.log10(numbers)
        logger.info("Using log10 scale")

    hist, bin_edges = np.histogram(numbers, bins=bins, range=range)

    # Calculate bin centers for output
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Output as TSV
    for center, count in zip(bin_centers, hist):
        if log and not log_values:
            center = 10 ** center
        ostream.write(f"{center}\t{count}\n")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-b", "--bins", type=int, default=10, help="number of bins")
    arg("-l", "--log", action="store_true", help="use log10 scale")
    arg("-L", "--log-values", action="store_true", help="display log10 of x values")
    arg("--min", type=float, help="minimum value for binning")
    arg("--max", type=float, help="maximum value for binning")


if __name__ == "__main__":
    main.go(histogram, setup_args)
