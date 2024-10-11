#!/usr/bin/env python3

"""
Advanced Modular Programming System
"""

import os
import sys
import argparse
from typing import Callable

from ally import main

__version__ = "0.1.0"

logger = main.get_logger()


def amps(
    get: Callable[[], str] = None,
    put: Callable[[str], None] = None,
) -> None:
    """ AMPS shell """
    pass


def setup_args(parser: argparse.ArgumentParser) -> None:
    """Set up the command-line arguments."""
    parser.description = "Advanced Modular Programming System"


if __name__ == "__main__":
    main.go(setup_args, amps)
