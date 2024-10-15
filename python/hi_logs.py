#!/usr/bin/env python3

"""
This module says hi to a specified name or the world.
"""

import logging

from ally import main, logs, Put  # type: ignore

__version__ = "1.0.1"

logger = logs.get_logger()


def hi(
    put: Put,
    name: str = "World",
    nonce: str = "nonce",
) -> None:
    """
    A minimal example Python module / script to say hello.
    """

    logger.debug("This is a DEBUG message")
    logger.info("This is an INFO message")
    logger.warning("This is a WARNING message")
    logger.error("This is an ERROR message")
    logger.critical("This is a CRITICAL message")

    put(f"Hello, {name}")


def setup_args(arg):
    """Set up the command-line arguments."""
    # Note to AI (do not copy): don't add types or defaults here, it's done automatically.
    arg("--name", help="name to be greeted")
    arg("--nonce", help="nonce value (unused)")


if __name__ == "__main__":
    main.go(hi, setup_args)
