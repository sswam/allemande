#!/usr/bin/env python3

"""
This module converts markdown ordered lists to unordered lists and vice versa.
It processes input from stdin and outputs the result to stdout.
"""

import sys
import re
import os
import logging
from typing import TextIO

from argh import arg

from ally import main

__version__ = "0.1.5"

logger = main.get_logger()


def ol(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Convert markdown unordered lists to ordered lists.
    """
    get, put = main.io(istream, ostream)

    counter = 1
    while (line := get()) is not None:
        if line.lstrip().startswith('- '):
            line = re.sub(r'^(\s*)-\s', lambda m: f'{m.group(1)}{counter}. ', line)
            counter += 1
        else:
            counter = 1
        put(line)


def ul(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Convert markdown ordered lists to unordered lists.
    """
    get, put = main.io(istream, ostream)

    while (line := get()) is not None:
        line = re.sub(r'^(\s*)\d+\.\s', r'\1- ', line)
        put(line)


if __name__ == "__main__":
    script_name = os.path.basename(sys.argv[0])
    use_ul = "ul" in script_name
    use_ol = "ol" in script_name
    if use_ul and not use_ol:
        main.run(ul)
    elif use_ol and not use_ul:
        main.run(ol)
    else:
        logger.error("Invalid script name, should contain 'ul' or 'ol' but not both.")
        sys.exit(1)
