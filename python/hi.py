#!/usr/bin/env python3

"""
hi.py - A minimal example Python module / script to say hello,
"""

import sys
import logging
from typing import TextIO

from argh import arg

from ally import main

__version__ = "1.0.0"

logger = main.get_logger()


@arg("--name", help="name to be greeted")
def hi(
    ostream: TextIO = sys.stdout,
    name: str = "World",
) -> None:
    """
    A minimal example Python module / script to say hello,
    """
    logger.debug(f"Greetings, {name}")

    print(f"Hello, {name}", file=ostream)


if __name__ == "__main__":
    main.run(hi)
