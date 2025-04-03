#!/usr/bin/env python3-allemande

"""
Lookup values from a lookup table file using keys from standard input.
"""

import sys
import logging
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


def lookup(lookup_file: str, istream: TextIO, ostream: TextIO, missing_ok: bool=False) -> None:
    """Process keys from input stream and print corresponding values from lookup file."""
    lookup_dict = {}

    with open(lookup_file, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip("\n")
            try:
                key, value = line.split('\t', 1)
                lookup_dict[key] = value
            except ValueError:
                logger.warning("Skipping malformed line in lookup file: %s", line.strip())

    for line in istream:
        key = line.strip()
        try:
            ostream.write(f"{lookup_dict[key]}\n")
        except KeyError:
            if not missing_ok:
                raise


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("lookup_file", help="file containing key-value pairs (tab-separated)")
    arg("--missing-ok", "-m", action="store_true", help="ignore missing keys instead of raising an error")


if __name__ == "__main__":
    main.go(lookup, setup_args)
