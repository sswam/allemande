#!/usr/bin/env python3-allemande

"""
Convert TSV data to an HTML table, with optional header row handling.
"""

import sys
import logging
import html
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


def format_table_row(cells: list[str], tag: str = "td") -> str:
    """Format a row of cells using the specified HTML tag."""
    escaped_cells = [html.escape(cell) for cell in cells]
    cells_html = f"<{tag}>" + f"</{tag}><{tag}>".join(escaped_cells) + f"</{tag}>"
    return f"  <tr>{cells_html}</tr>"


def tsv2html(istream: TextIO, ostream: TextIO, no_head: bool = False) -> None:
    """Convert TSV input to HTML table output."""

    lines = [line.rstrip("\n").split("\t") for line in istream]
    if not lines:
        return

    ostream.write("<table>\n")

    if not no_head:
        ostream.write("<thead>\n")
        ostream.write(format_table_row(lines[0], "th") + "\n")
        ostream.write("</thead>\n")
        lines = lines[1:]

    ostream.write("<tbody>\n")
    for row in lines:
        ostream.write(format_table_row(row) + "\n")
    ostream.write("</tbody>\n")
    ostream.write("</table>\n")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-H", "--no-head", action="store_true",
        help="treat all rows as data (no header)")


if __name__ == "__main__":
    main.go(tsv2html, setup_args)
