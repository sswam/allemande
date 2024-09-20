#!/usr/bin/env python

"""
cat_named.py - A Python script to concatenate and display file contents with customizable headers.

This script can be used to read and display the contents of multiple files,
with options to add headers, numbering, and customize the output format.

Usage:
    python cat_named.py [OPTIONS] FILE1 [FILE2 ...]

This script can also be used as a module:
    from cat_named import cat_named
"""

import os
import sys
from pathlib import Path

from argh import arg

from ally import main

__version__ = "1.0.0"


logger = main.get_logger()


@arg('files', nargs='*', help='Files to concatenate and display')
@arg('--header-pre', help='Prefix for the header line')
@arg('--header-post', help='Suffix for the header line')
@arg('--footer', help='String to append after each file\'s content')
@arg('--number', help='Number the files starting from this value')
@arg('--number-post', help='String to append after the number in the header')
@arg('--path', help='Search for files in PATH', action='store_true')
@arg('--basename', help='Use only the basename of the file in the header', action='store_true')
@arg('-n', '--stdin-name', help='Use this name for stdin')
def cat_named(files, header_pre='## File: ', header_post='\n\n', footer='\n\n', number=None, number_post=". ", path=False, basename=False, stdin_name='input'):
    """
    Concatenate and return file contents with customizable headers.
    """
    if number is not None:
        number = int(number)

    result = []

    for file in files:
        with main.TextInput(file, search=path, basename=basename, stdin_name=stdin_name) as input:
            if number is not None:
                result.append(f"{header_pre}{number}{number_post}{input.display}{header_post}")
                number += 1
            else:
                result.append(f"{header_pre}{input.display}{header_post}")
            result.append(input.read())
            result.append(footer)

    text = "".join(result)

    return text


if __name__ == "__main__":
    main.run(cat_named)
