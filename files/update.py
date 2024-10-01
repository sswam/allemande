#!/usr/bin/env python3

"""
This module updates a file with new content from a string or file.
If content is unchanged, the file is not modified and mtime remains the same.
"""

import sys
import os
import re
from typing import TextIO

from argh import arg
from ally import main

__version__ = "0.1.3"  # Bumped patch version

logger = main.get_logger()


def read_content(filename: str) -> str:
    """Read content from a file."""
    try:
        with open(filename, 'r') as f:
            return f.read()
    except IOError as e:
        logger.error(f"Error reading file {filename}: {e}")
        raise


@arg('filename', help="The file to update")
@arg('-c', '--content', help="The new content to write to the file")
@arg('-f', '--file', help="File to read new content from (default stdin)")
@arg('-E', '--no-eol', help="Don't add a newline at the end of the file", action='store_true')
@arg('-K', '--no-keep-time', help="Don't keep the original file's mtime and atime", dest='keep_time', action='store_false')
def update(
    filename: str,
    content: str = None,
    file: str = None,
    no_eol: bool = False,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout
    keep_time: bool = True
) -> None:
    """
    Update a file with new content.
    If content is not provided directly, it will be read from a file or stdin.
    """
    get, put = main.io(istream, ostream)

    if file:
        content = read_content(file)
    elif content is None:
        logger.info("Reading content from stdin")
        content = istream.read()

    if not no_eol and not content.endswith('\n'):
        content += '\n'

    # Check if content is unchanged
    if os.path.exists(filename) and read_content(filename) == content:
        return

    # Write content to file
    try:
        with open(filename, 'w') as f:
            f.write(content)
    except IOError as e:
        logger.error(f"Error writing to file {filename}: {e}")
        raise

    # set mtime and atime to original file's values unless told otherwise
    if file and keep_time:
        os.utime(filename, (os.path.getatime(file), os.path.getmtime(file)))


if __name__ == '__main__':
    main.run(update)
