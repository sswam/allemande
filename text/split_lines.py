#!/usr/bin/env python3
"""
split_lines - split a file into separate files based on a pattern

Reads a file (or stdin) and splits lines matching pattern into separate files.
Lines like "identifier: content" become files named "identifier" containing "content".
"""

import sys
import re
from pathlib import Path
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.2"

logger = logs.get_logger()


def split_lines(
    input_file: TextIO,
    pattern: str = r":\s+",
    extension: str = "",
    comments: bool = False,
) -> None:
    """Split input lines into separate files based on pattern."""
    regex = re.compile(pattern)
    line_num = 0
    processed = 0
    skipped = 0
    skip_comments = not comments

    for line in input_file:
        line_num += 1
        line = line.rstrip('\n')
        if skip_comments and line.startswith('#'):
            skipped += 1
            continue

        match = regex.split(line, 1)
        if len(match) != 2:
            logger.debug("Skipping malformed line %d: %s", line_num, line[:50])
            skipped += 1
            continue

        identifier, content = match
        if not identifier:
            logger.debug("Skipping line %d with empty identifier", line_num)
            skipped += 1
            continue

        filename = identifier + extension
        try:
            Path(filename).write_text(content + '\n', encoding='utf-8')
            processed += 1
        except OSError as e:
            logger.error("Failed to write %s: %s", filename, e)
            raise

    logger.info("Processed %d lines, skipped %d", processed, skipped)


def setup_args(arg):
    """Set up command-line arguments."""
    arg('input_file', nargs='?', type=main.argparse.FileType('r'),
        default=sys.stdin, help='input file (default: stdin)')
    arg('--pattern', '-p', default=r':\s+',
        help='regex pattern to split on (default: ":\\s+")')
    arg('--extension', '-x', default='',
        help='file extension to add (default: none)')
    arg('--comments', '-c', action='store_true',
        help='enable splitting out lines starting with #')


if __name__ == '__main__':
    main.go(split_lines, setup_args)
