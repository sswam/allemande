#!/usr/bin/env python3-allemande

"""
Convert blocks of text (separated by blank lines) to TSV format, escaping tabs and backslashes.
"""

import sys
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


def escape_field(text: str) -> str:
    """Escape tabs and backslashes in a field."""
    return text.replace('\\', '\\\\').replace('\t', '\\t')


def block2tsv(istream: TextIO, ostream: TextIO) -> None:
    """Convert blocks of text from input to TSV lines in output."""
    current_block: list[str] = []

    def write_block(block):
        escaped_fields = [escape_field(field) for field in block]
        ostream.write('\t'.join(escaped_fields) + '\n')

    for line in istream:
        line = line.rstrip('\n')
        if not line and current_block:
            write_block(current_block)
            current_block = []
            continue
        if line:
            current_block.append(line)

    # Handle last block if not empty and not terminated by blank line
    if current_block:
        write_block(current_block)

def setup_args(arg):
    """Set up command-line arguments."""
    pass  # No arguments needed, works with stdin/stdout


if __name__ == "__main__":
    main.go(block2tsv, setup_args)
