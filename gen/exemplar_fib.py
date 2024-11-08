#!/usr/bin/env python3-allemande

"""
This module demonstrates best practices for Python scripting.
It includes a function to calculate Fibonacci numbers and print them.
"""

import sys
import logging
from typing import TextIO

from argh import arg
from ally import main

__version__ = "0.1.0"

logger = main.get_logger()


def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n - 1) + fibonacci(n - 2)


@arg("--count", help="number of Fibonacci numbers to generate", type=int)
def print_fibonacci(
    *filenames: str,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    count: int = 10
) -> None:
    """
    Generate and print Fibonacci numbers.

    This function demonstrates:
    - Using argh for argument parsing
    - Handling stdin/stdout
    - Proper logging
    - Type hinting
    - Docstrings
    """
    get, put = main.io(istream, ostream)

    if count < 0:
        logger.error("Count must be non-negative")
        raise ValueError("Count must be non-negative")

    logger.info(f"Generating {count} Fibonacci numbers")

    for i in range(count):
        fib_num = fibonacci(i)
        put(f"Fibonacci({i}) = {fib_num}")

    if filenames:
        logger.warning("File processing not implemented in this example")

    # TODO: Implement file processing functionality
    # FIXME: Optimize Fibonacci calculation for large numbers
    # XXX: Consider adding memoization for performance


if __name__ == "__main__":
    main.run(print_fibonacci)
