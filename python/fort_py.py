#!/usr/bin/env python3-allemande

"""
This module selects a random line from standard input.
"""

import sys
import random
from typing import TextIO

from argh import arg

from ally import main

__version__ = "0.1.0"

logger = main.get_logger()


@arg("--seed", help="random seed for reproducibility")
def fort(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    seed: int = None,
) -> None:
    """
    Select a random line from standard input and print it.
    """
    if seed is not None:
        random.seed(seed)

    get, put = main.io(istream, ostream)

    n = 0
    selected_line = None

    for line in istream:
        n += 1
        if random.randint(0, n - 1) == 0:
            selected_line = line

    if selected_line is not None:
        put(selected_line, end="")


if __name__ == "__main__":
    main.run(fort)
