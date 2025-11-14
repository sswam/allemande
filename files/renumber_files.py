#!/usr/bin/env python3-allemande

"""
Renumber files by replacing or prepending sequential numbers to filenames.
"""

import re
from pathlib import Path
import tempfile
import os

from ally import main  # type: ignore

__version__ = "0.1.2"


def renumber_files(
    files: list[str],
    width: int = 1,
    start: int = 0,
    prepend: bool = False,
) -> None:
    """
    Renumber files in order, replacing numeric prefix or prepending number.

    For each file, either replace the leading number (with optional separator)
    or prepend a new number with a dash separator.
    """
    # Pattern to match leading digits and optional separator
    pattern = re.compile(r'^(\d+)([ \-_,])?')

    # Build list of renames
    renames = []
    counter = start

    for filepath in files:
        path = Path(filepath)
        name = path.name
        parent = path.parent

        if prepend:
            # Always prepend, never touch existing numbers
            new_name = f"{counter:0{width}d}-{name}"
        else:
            match = pattern.match(name)

            if match:
                # Replace existing number, keep separator if present
                separator = match.group(2) or ""
                remainder = name[match.end():]
                new_name = f"{counter:0{width}d}{separator}{remainder}"
            else:
                # No number found, prepend number with dash
                new_name = f"{counter:0{width}d}-{name}"

        new_path = parent / new_name
        renames.append((path, new_path))
        counter += 1

    # Perform renames, using temp names to avoid collisions
    for old_path, new_path in renames:
        if old_path == new_path:
            continue

        # Create temp file in same directory to ensure same filesystem
        temp_fd, temp_path_str = tempfile.mkstemp(
            dir=new_path.parent,
            prefix='.tmp_renumber_',
            suffix=f'_{new_path.name}'
        )
        os.close(temp_fd)  # Close the file descriptor, we just need the path
        temp_path = Path(temp_path_str)

        try:
            old_path.rename(temp_path)
            temp_path.rename(new_path)
        except Exception:
            # Clean up temp file if something goes wrong
            if temp_path.exists():
                temp_path.unlink()


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("files", nargs="*", help="files to renumber")
    arg("-w", "--width", type=int, help="zero-padding width for numbers (default: no padding)")
    arg("-s", "--start", type=int, help="starting number")
    arg("-p", "--prepend", action="store_true", help="always prepend number, never replace existing numbers")


if __name__ == "__main__":
    main.go(renumber_files, setup_args)
