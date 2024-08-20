#!/usr/bin/env python

import sys
import logging

import argh
from wcwidth import wcswidth


logger = logging.getLogger(__name__)


"""
Markdown Table Formatter

CLI Usage:
    echo "your_markdown_table" | python markdown_table_spacing.py --compact True/False

Args:
    --compact: If True, generates a compact table with minimal spacing.
               If False (default), aligns contents neatly with padded spacing.
"""


def parse_table(md):
    """
    Parses a Markdown table into its components.

    Args:
        md (str): The Markdown table to be parsed.

    Returns:
        tuple: headers, aligns, and rows of the table.
    """
    lines = md.strip().split('\n')
    headers = [cell.strip() for cell in lines[0].strip('|').split('|')]
    aligns = [cell.strip() for cell in lines[1].strip('|').split('|')]
    rows = [[cell.strip() for cell in line.strip('|').split('|')] for line in lines[2:]]
    return headers, aligns, rows


def format_table(headers, aligns, rows, compact=False):
    """
    Formats a Markdown table with proper spacing.

    Args:
        headers (list): Column headers.
        aligns (list): Alignment indicators.
        rows (list): Table rows.

    Returns:
        str: The formatted Markdown table.
    """
    if compact:
        col_widths = [1] * len(headers)
    else:
        col_widths = [wcswidth(h) for h in headers]
        for row in rows:
            col_widths = [max(w, wcswidth(cell)) for w, cell in zip(col_widths, row)]

    def format_line(cells):
        """
        Formats a single row or header line with appropriate spacing.

        Args:
            cells (list): The elements of the row.

        Returns:
            str: The formatted row.
        """
        padded_cells = []
        for i, cell in enumerate(cells):
            pad_length = col_widths[i] - wcswidth(cell)
            padded_cell = cell + ' ' * pad_length
            padded_cells.append(padded_cell)
        return '| ' + ' | '.join(padded_cells) + ' |'

    header_line = format_line(headers)
    align_line = '|' + '|'.join('-' * (col_widths[i] + 2) for i in range(len(headers))) + '|'
    row_lines = [format_line(row) for row in rows]

    return '\n'.join([header_line, align_line] + row_lines)


def fix_spacing(compact, markdown):
    """
    Adjusts the spacing in a Markdown table.

    Args:
        compact (bool): If True, generates a compact version of the table with minimal spacing.
                        If False, pads contents to align columns neatly.
        markdown (str): The Markdown table to be transformed.

    Returns:
        str: The transformed Markdown table.
    """

    headers, aligns, rows = parse_table(markdown)

    return format_table(headers, aligns, rows, compact=compact)


def main(compact: bool = False):
    """
    Main function to handle command-line arguments.

    Args:
        compact (bool): If True, produces a compact table.
                        If False (default), aligns with spacing.
    """
    markdown = sys.stdin.read()
    print(fix_spacing(compact, markdown.strip()))


if __name__ == '__main__':
    try:
        argh.dispatch_command(main)
    except Exception as e:
        logger.error(e)
