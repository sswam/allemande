#!/usr/bin/env python3

"""
This module converts TSV (Tab-Separated Values) to formatted text.
It supports multiple tables in input with the -m option.
"""

import os
import sys
import re
import logging
from typing import TextIO
from dataclasses import dataclass, field

from argh import arg
from ally import main

__version__ = "1.1.7"

logger = main.get_logger()


@dataclass
class Options:
    multi_table: bool = False
    gap: int = 2
    format_options: list[str] = field(default_factory=list)


def get_tsv_format() -> re.Pattern:
    """Return the TSV format regex based on environment variable."""
    tsv_format = os.environ.get("TSV_FORMAT", "")
    if tsv_format == "spaces_ok":
        return re.compile(r"\s{2,}|\t")
    elif tsv_format == "strict":
        return re.compile(r"\t")
    else:
        return re.compile(r" *\t")


def process_row(row: list[str], width: list[int], options: list[str]) -> None:
    """Process a single row, updating column widths."""
    for i, cell in enumerate(row):
        if cell == "\0":
            row[i] = "[NULL]"
        opt = options[i] if i < len(options) else "{}"
        try:
            formatted_cell = opt.format(cell)
        except (ValueError, IndexError, KeyError):
            formatted_cell = str(cell)
        length = len(formatted_cell)
        if i < len(width):
            width[i] = max(width[i], length)
        else:
            width.append(length)


def adjust_options(options: list[str], width: list[int]) -> None:
    """Adjust format options based on column widths."""
    # Extend options to match the number of columns
    while len(options) < len(width):
        options.append("{}")
    for i in range(len(width)):
        opt = options[i]
        if not re.search(r'(\d+|\.\d+)[dfgeswx]', opt, re.IGNORECASE):
            options[i] = f"{{:<{width[i]}}}"


def print_formatted_rows(rows: list[list[str]], format_str: str, option_count: int, ostream: TextIO) -> None:
    """Print formatted rows."""
    empty = [""] * option_count
    for row in rows:
        line = format_str.format(*(row + empty)[:option_count])
        if not row:
            line = ""
        elif line.strip() == "":
            line = " "
        else:
            line = line.rstrip()
        print(line, file=ostream)


def process_chunk(chunk: list[str], gap: int, format_options: list[str], ostream: TextIO) -> None:
    """Process a chunk of TSV data."""
    width = []
    rows = []
    options = format_options.copy()

    for line in chunk:
        row = re.split(get_tsv_format(), line.strip())
        process_row(row, width, options)
        rows.append(row)

    if not options:
        # Generate default options based on width
        options = [f"{{:>{w}}}" for w in width]

    adjust_options(options, width)
    format_str = (" " * gap).join(options)
    print_formatted_rows(rows, format_str, len(options), ostream)


def split_into_chunks(istream: TextIO, multi_table: bool) -> list[list[str]]:
    """Split input stream into chunks based on multi-table option."""
    rx_split = get_tsv_format()
    chunks = []
    current_chunk = []

    for line in istream:
        if multi_table and not rx_split.search(line):
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = []
            chunks.append([line.strip()])
        else:
            current_chunk.append(line.strip())

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


@arg('-m', '--multi-table', help='Support multiple tables in input')
@arg('-g', '--gap', type=int, default=2, help='Set gap between columns')
def tsv2txt(
    *format_options: str,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    multi_table: bool = False,
    gap: int = 2,
) -> None:
    """
    Convert TSV (Tab-Separated Values) to formatted text.
    Supports multiple tables in input with the -m option.
    """
    options = Options(multi_table=multi_table, gap=gap, format_options=list(format_options))

    # Process format_options
    for i, opt in enumerate(options.format_options):
        if not opt:
            opt = "-"
        if not opt[-1].isalpha():
            opt += "f" if "." in opt else "s"
        options.format_options[i] = f"{{:{opt}}}"

    chunks = split_into_chunks(istream, options.multi_table)
    for chunk in chunks:
        process_chunk(chunk, options.gap, options.format_options, ostream)


if __name__ == "__main__":
    main.run(tsv2txt)
