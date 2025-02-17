#!/usr/bin/env python3-allemande

"""
Convert TSV data to an HTML table.
"""

import sys
import logging
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


def tsv_to_html(file: TextIO, no_head: bool = False) -> str:
    """Convert TSV data to an HTML table string."""
    lines = file.readlines()
    if not lines:
        return "<table></table>"

    rows = [line.strip().split("\t") for line in lines]
    result = ["<table>"]

    if not no_head and len(rows) > 0:
        headers = rows[0]
        result.append("<thead>")
        result.append("<tr>")
        result.extend(f"<th>{h}</th>" for h in headers)
        result.append("</tr>")
        result.append("</thead>")
        rows = rows[1:]

    result.append("<tbody>")
    for row in rows:
        result.append("<tr>")
        result.extend(f"<td>{cell}</td>" for cell in row)
        result.append("</tr>")
    result.append("</tbody>")
    result.append("</table>")

    return "\n".join(result)


def tsv2html_table(file: TextIO = sys.stdin, no_head: bool = False) -> None:
    """Convert TSV input to HTML table output."""
    html = tsv_to_html(file, no_head)
    print(html)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-H", "--no-head", action="store_true",
        help="treat all rows as data (no header row)")


if __name__ == "__main__":
    main.go(tsv2html_table, setup_args)
