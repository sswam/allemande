#!/usr/bin/env python3

"""
This module renames files by adding a timestamp prefix.
"""

import os
import sys
import logging
from datetime import datetime
from typing import TextIO
import re

from argh import arg

from ally import main

__version__ = "0.1.0"

logger = main.get_logger()


def rename_file(filename: str) -> str:
    """
    Rename a file by adding a timestamp prefix.
    """
    try:
        # Split filename and extension
        name, extension = os.path.splitext(filename)

        # Get file modification time
        mtime = os.path.getmtime(filename)
        timestamp = datetime.fromtimestamp(mtime).strftime("%Y%m%d-%H%M%S")

        # Remove any existing timestamp
        name = re.sub(r"^\d{8}-\d{6}[-\.]", "", name)

        # Create new filename
        new_filename = f"{timestamp}.{name}{extension}"

        # Truncate if too long
        if len(new_filename) > 255:
            max_filename_length = 255 - len(extension)
            new_filename = new_filename[:max_filename_length] + extension

        return new_filename
    except Exception as e:
        logger.error(f"Error processing {filename}: {str(e)}")
        return filename


@arg("filenames", nargs='+', help="files to be renamed")
def renamer(
    *filenames: list[str],
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Rename files by adding a timestamp prefix.
    """
    if not filenames:
        logger.warning("No files provided for renaming.")
        return

    for filename in filenames:
        new_filename = rename_file(filename)
        if new_filename != filename:
            try:
                os.rename(filename, new_filename)
                logger.info(f"Renamed: {filename} -> {new_filename}")
            except OSError as e:
                logger.error(f"Failed to rename {filename}: {str(e)}")
        else:
            logger.info(f"Skipped: {filename}")


if __name__ == "__main__":
    main.run(renamer)
