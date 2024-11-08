#!/usr/bin/env python3-allemande

"""
This module performs text substitution with various options.
"""

import sys
import os
import re
import logging
from typing import TextIO

from argh import arg
from ally import main

__version__ = "1.0.0"

logger = main.get_logger()


def read_file_content(filename: str) -> str:
    """Read and return the content of a file."""
    with open(filename, 'r') as file:
        return file.read()


def process_mapping(args: list[str], reverse: bool, file_content: bool) -> dict[str, str]:
    """Process the mapping from command-line arguments or file."""
    mapping = {}
    while len(args) >= 2:
        k, v = args[:2]
        args = args[2:]
        if reverse:
            k, v = v, k
        if file_content:
            k = read_file_content(k)
            v = read_file_content(v)
        mapping[k] = v
    return mapping


def build_regex(mapping: dict[str, str], whole_words: bool) -> str:
    """Build the regex pattern for substitution."""
    patterns = []
    for k in mapping.keys():
        pattern = re.escape(k)
        if whole_words:
            pattern = fr'\b{pattern}\b'
        patterns.append(pattern)
    return '|'.join(patterns)


@arg('-w', '--whole-words', help='Match whole words only')
@arg('-e', '--use-env', help='Use environment variables as mapping')
@arg('-q', '--quote-chars', help='Specify quote characters for keys')
@arg('-m', '--map-file', help='Read mapping from file')
@arg('-r', '--reverse', help='Reverse key-value pairs')
@arg('-f', '--file-content', help='Treat key-value pairs as filenames and read their contents')
def sub(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    whole_words: bool = False,
    use_env: bool = False,
    quote_chars: str = '',
    map_file: str = '',
    reverse: bool = False,
    file_content: bool = False,
    *args: str
) -> None:
    """
    Perform text substitution based on various options and a mapping.
    It reads from STDIN and writes to STDOUT.
    """
    mapping = {}

    if use_env:
        mapping = dict(os.environ)

    if map_file:
        with open(map_file, 'r') as f:
            for line in f:
                k, v = line.strip().split('\t', 1)
                mapping[k] = v

    mapping.update(process_mapping(list(args), reverse, file_content))

    q0, q1 = quote_chars[:2] if quote_chars else ('', '')
    mapping = {f"{q0}{k}{q1}": v for k, v in mapping.items()}

    regex = build_regex(mapping, whole_words)
    logger.debug(f"Regex pattern: {regex}")

    def replace(match):
        return mapping[match.group(0)]

    get, put = main.io(istream, ostream)

    # TODO: Handle multiline mode if needed
    for line in istream:
        modified_line = re.sub(regex, replace, line) if regex else line
        put(modified_line, end='')


if __name__ == "__main__":
    main.run(sub)
