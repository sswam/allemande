#!/usr/bin/env python3

"""
Find files without proper header comments.
"""

import os
import sys
import argparse
import logging
from typing import TextIO, Callable
import subprocess

from argh import arg
from ally import main

__version__ = "0.1.1"

logger = main.get_logger()

MIN_HEADER_LENGTH = 10

extensions = [ "py", "sh", "c", "pl" ]
comments = { "#", "//", "/*", '"""' }


def check_file_header(file_path: str) -> bool:
    """Check if the file has a proper header comment."""
    try:
        with open(file_path, 'r') as file:
            for _ in range(3):
                line = file.readline().strip()
                # check for any of the comments
                if line and line.startswith(tuple(comments)) and len(line) > MIN_HEADER_LENGTH:
                    return True
                # also accespt python """\ncomments\n"""
                if line and line.startswith('"""'):
                    line = file.readline().strip()
                    if len(line) > MIN_HEADER_LENGTH:
                        return True
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return True  # don't mess with binary files
    return False


@arg('-i', '--info', help='Enable extra info output')
def find_no_header_comment(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    info: bool = False
) -> None:
    """Find files without proper header comments."""
    get, put = main.io(istream, ostream)

    while file := get():
        if os.path.islink(file):
            continue
        if not os.path.exists(file):
            logger.error(f"File not found: {file}")
            continue
        if os.path.isdir(file):
            logger.debug(f"Skipping directory: {file}")
            continue
        if not os.path.isfile(file):
            logger.debug(f"Not a regular file: {file}")
            continue
        if not any(file.endswith(f".{ext}") for ext in extensions):
            logger.debug(f"Skipping file: {file}")
            continue
        if check_file_header(file):
            continue

        if info:
            output = subprocess.check_output(
                f"head -n 4 {file} | batcat --color=always --style header --tabs 8 -l bash --file-name {file}",
                shell=True, text=True
            )
            put(output)
        else:
            put(file)


if __name__ == "__main__":
    main.run(find_no_header_comment)
