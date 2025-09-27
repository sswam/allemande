#!/usr/bin/env python3-allemande

"""
Count frequency of values from stdin, one per line.
"""

from collections import Counter
from typing import TextIO

from ally import main, logs

__version__ = "0.1.2"

logger = logs.get_logger()


def read_values(istream: TextIO) -> list[float]:
    """Read values from input stream, one per line."""
    values = []
    for line in istream:
        try:
            num = float(line.strip())
            values.append(num)
        except ValueError:
            logger.warning("Skipping invalid number: %s", line.strip())
    return values


def frequency(
    istream: TextIO,
    ostream: TextIO,
    cumulative: bool = False,
    scaled: bool = False,
) -> None:
    """
    Output frequency of each value, sorted.

    Args:
        istream: Input stream to read values from
        ostream: Output stream to write results to
        cumulative: Whether to include cumulative frequencies
        scaled: Whether to scale frequencies to 0-1 range
    """
    values = read_values(istream)
    if not values:
        raise ValueError("No valid numbers found in input")

    counts = Counter(values)
    total = len(values)
    cum_sum = 0

    for value, count in sorted(counts.items()):
        cum_sum += count
        if cumulative:
            cum_freq = cum_sum/total if scaled else cum_sum
            ostream.write(f"{value}\t{count}\t{cum_freq:.3f}\n")
        else:
            freq = count/total if scaled else count
            ostream.write(f"{value}\t{freq:.3f}\n")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-c", "--cumulative", action="store_true",
        help="include cumulative frequency")
    arg("-s", "--scaled", action="store_true",
        help="scale cumulative frequency to 0-1 range")


if __name__ == "__main__":
    main.go(frequency, setup_args)
