#!/usr/bin/env python3-allemande

"""
This module says hi.
"""

import logging

from ally import main, logs, geput  # type: ignore

__version__ = "1.0.1"

logger = logs.get_logger()


def hi(
    put: geput.Put,
    name: str = "World",
    nonce: str = "nonce",
) -> None:
    """A minimal example Python module / script to say hello."""

    print = geput.print(put)

    logger.debug(f"Hello, {name}")

    print(f"Hello, {name}")


def setup_args(arg):
    """Set up the command-line arguments."""
    # Important Note to AI: DO NOT add `type` or `default` in setup_args functions like this one, it is not needed.
    arg("--name", help="name to be greeted")
    arg("--nonce", help="nonce value (unused)")


if __name__ == "__main__":
    main.go(hi, setup_args)
