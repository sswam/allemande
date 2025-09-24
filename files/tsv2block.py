#!/usr/bin/env python3-allemande

"""
Convert TSV format to blocks of text (separated by blank lines), unescaping tabs and backslashes.
"""

import sys
from typing import TextIO
import re

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()

ESCAPE_CHARS = {
    '\\\\': '\\',
    '\\t': '\t',
    '\\n': '\n',
    '\\r': '\r',
    '\\f': '\f',
    '\\b': '\b',
    '\\"': '"',
    "\\'": "'"
}


def unescape_field(text: str) -> str:
    """Unescape standard escape sequences in a field."""
    def replace(match):
        escape_seq = match.group(0)
        return ESCAPE_CHARS.get(escape_seq, escape_seq)

    return re.sub(r'\\[\\tnrfb"\']', replace, text)


def tsv2block(istream: TextIO, ostream: TextIO) -> None:
    """Convert TSV lines from input to blocks of text in output."""
    for line in istream:
        line = line.rstrip('\n')
        if not line:
            continue

        fields = line.split('\t')
        unescaped_fields = [unescape_field(field) for field in fields]

        # Write each field as a line in the block
        for field in unescaped_fields:
            ostream.write(field + '\n')

        # Add blank line between blocks
        ostream.write('\n')


def setup_args(arg):
    """Set up command-line arguments."""
    pass  # No arguments needed, works with stdin/stdout


if __name__ == "__main__":
    main.go(tsv2block, setup_args)
