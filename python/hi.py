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
@arg("--nonce", help="name to be greeted")
def hi(
    ostream: TextIO = sys.stdout,
    name: str = "World",
    nonce: str = "nonce",
) -> None:
    """
    A minimal example Python module / script to say hello,
    """

    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")

    print(f"Hello, {name}", file=ostream)


if __name__ == "__main__":
    main.run(hi)
