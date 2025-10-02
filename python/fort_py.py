#!/usr/bin/env python3-allemande

"""
Select a random line from standard input.
"""

import sys
import random
from typing import TextIO

from ally import main

__version__ = "0.1.1"

logger = main.get_logger()


def fort(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    seed: int | None = None,
) -> None:
    """Select a random line from standard input and print it."""
    if seed is not None:
        random.seed(seed)

    n = 0
    selected_line = None

    for line in istream:
        n += 1
        if random.randint(0, n - 1) == 0:
            selected_line = line

    if selected_line is not None:
        print(selected_line.rstrip("\n"), file=ostream)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("--seed", type=int, help="random seed for reproducibility")


if __name__ == "__main__":
    main.go(fort, setup_args)
