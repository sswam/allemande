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

import argh

__version__ = "1.0.0"

def find_in_path(file):
    """
    Find a file in the system PATH.

    Args:
        file (str): The name of the file to find.

    Returns:
        str: The full path to the file if found.

    Raises:
        FileNotFoundError: If the file is not found in PATH.
    """
    for dir in os.environ['PATH'].split(os.pathsep):
        full_path = Path(dir) / file
        if full_path.is_file():
            return str(full_path)
    raise FileNotFoundError(f"{file} (in $PATH)")

@argh.arg('files', nargs='*', help='Files to concatenate and display')
@argh.arg('--header-pre', help='Prefix for the header line')
@argh.arg('--header-post', help='Suffix for the header line')
@argh.arg('--footer', help='String to append after each file\'s content')
@argh.arg('--number', help='Number the files starting from this value')
@argh.arg('--number-post', help='String to append after the number in the header')
@argh.arg('--path', help='Search for files in PATH', action='store_true')
@argh.arg('--basename', help='Use only the basename of the file in the header', action='store_true')
def cat_named(files, header_pre='# ', header_post=':\n\n', footer='\n\n', number=None, number_post=". ", path=False, basename=False):
    """
    Concatenate and display file contents with customizable headers.

    Args:
        files (list): Paths to the files to be read and displayed.
        header_pre (str): Prefix for the header line.
        header_post (str): Suffix for the header line.
        footer (str): String to append after each file's content.
        number (int): If provided, number the files starting from this value.
        number_post (str): String to append after the number in the header.
        path (bool): If True, search for files in PATH.
        basename (bool): If True, use only the basename of the file in the header.

    Returns:
        str: Concatenated contents of all files with headers.
    """
    if number is not None:
        number = int(number)
    result = ""
    for file in files:
        if path:
            file = find_in_path(file)
        file_path = Path(file)
        name = file_path.name if basename else str(file_path)

        if number is not None:
            result += f"{header_pre}{number}{number_post}{name}{header_post}"
            number += 1
        else:
            result += f"{header_pre}{name}{header_post}"

        with file_path.open('r') as istream:
            result += istream.read()
        result += footer

    return result

if __name__ == "__main__":
    try:
        argh.dispatch_command(cat_named)
    except BaseException as e:
        print(f"Error: {type(e).__name__} {str(e)}", file=sys.stderr)
        sys.exit(1)
