#!/usr/bin/env python3

"""
This module splits stdin into files based on the first TSV column or specified columns.
"""

import sys
import logging
from typing import TextIO
from pathlib import Path

from argh import arg

from ally import main

__version__ = "0.1.0"

logger = main.get_logger()


def get_output_filename(columns: list[str], sep: str, ext: str) -> str:
    """Generate the output filename based on specified columns and separator."""
    return f"{sep.join(columns)}{ext}"


@arg("--ext", "-x", help="File extension for output files", default="")
@arg("--columns", "-c", help="Comma-separated list of columns to use for filenames", default="1")
@arg("--sep", "-s", help="Separator for joining multiple columns", default="__")
@arg("--keep", "-k", help="Keep the filename columns in the output", action="store_true")
@arg("--head", "-H", help="Use column names instead of numbers (assumes first row is header)", action="store_true")
def split_column(
    *filenames: str,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    ext: str = "",
    columns: str = "1",
    sep: str = "__",
    keep: bool = False,
    head: bool = False,
) -> None:
    """
    Split stdin into files with names from specified TSV columns.
    """
    get, put = main.io(istream, ostream)

    # Process column specification
    col_indices = [int(c) - 1 for c in columns.split(",")]

    # Initialize variables
    header = None
    file_handles = {}

    try:
        for line_num, line in enumerate(get, start=1):
            fields = line.strip().split("\t")

            if head and line_num == 1:
                header = fields
                continue

            if len(fields) <= max(col_indices):
                logger.warning(f"Line {line_num}: Not enough fields, skipping")
                continue

            if head:
                filename_parts = [fields[header.index(col)] for col in columns.split(",")]
            else:
                filename_parts = [fields[i] for i in col_indices]

            output_filename = get_output_filename(filename_parts, sep, ext)

            if output_filename not in file_handles:
                file_handles[output_filename] = open(output_filename, "w")

            if not keep:
                output_fields = [f for i, f in enumerate(fields) if i not in col_indices]
            else:
                output_fields = fields

            file_handles[output_filename].write("\t".join(output_fields) + "\n")

    finally:
        # Close all open file handles
        for fh in file_handles.values():
            fh.close()

    logger.info(f"Split input into {len(file_handles)} files")


if __name__ == "__main__":
    main.run(split_column)
