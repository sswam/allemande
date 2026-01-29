#!/usr/bin/env python3-allemande

"""
This module flattens a tree of files by renaming them to the current directory with path separators replaced by a separator.
"""

import os
import shutil
import subprocess
from typing import TextIO

from ally import main  # type: ignore


def flatten_tree(
    istream: TextIO,
    ostream: TextIO,
    sep: str = "__",
) -> None:
    """Flatten file paths from stdin by stripping prefixes and replacing / with sep, moving to current dir."""
    for line in istream:
        original_path = line.strip()
        if not original_path:
            continue

        # Strip leading ./ or ../ prefixes
        path = original_path
        while path.startswith('./') or path.startswith('../'):
            if path.startswith('./'):
                path = path[2:]
            elif path.startswith('../'):
                path = path[3:]

        # Replace / with sep to get target name
        target_name = path.replace('/', sep)

        # Move file to current directory with new name
        shutil.move(original_path, target_name)

        # Try to remove source directories if empty
        dirname = os.path.dirname(original_path)
        if dirname:
            subprocess.run(['rmdir', '-p', dirname], stderr=subprocess.DEVNULL)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-s", "--sep", help="separator for flattening")


if __name__ == "__main__":
    main.go(flatten_tree, setup_args)
