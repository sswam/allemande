#!/usr/bin/env python3-allemande

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
from ally import main, logs  # type: ignore

__version__ = "1.1.11"

logger = logs.get_logger()


@dataclass
class Options:
	multi_table: bool = False
	gap: str = "  "
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
		if i == 0:
			# Count leading tabs as 8 spaces for layout purposes
			leading_tabs = len(cell) - len(cell.lstrip('\t'))
			length += leading_tabs * 7  # 7 because the tab itself counts as 1
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
		if row:
			# Preserve leading tabs in the first column
			dedented = row[0].lstrip('\t')
			leading_tabs = len(row[0]) - len(dedented)
			# add back equivalent spaces for layout purposes
			row[0] = " " * (leading_tabs * 8) + dedented
			line = format_str.format(*(row + empty)[:option_count])
			# put back leading tabs
			line = '\t' * leading_tabs + line[leading_tabs * 8:]
		else:
			line = ""
		# IDK what this code was for, but it's now annoying me so I'll comment it out!
		# Why replace an empty line with a single space?!
# 		if line.strip() == "":
# 			line = " "
# 		else:
# 			line = line.rstrip()
		line = line.rstrip()
		print(line, file=ostream)


def process_table(table: list[str], gap: str, format_options: list[str], ostream: TextIO) -> None:
	"""Process a table of TSV data."""
	width = []
	rows = []
	options = format_options.copy()

	for line in table:
		dedented = line.lstrip('\t')
		leading_tabs = len(line) - len(dedented)
		row = re.split(get_tsv_format(), dedented)
		if row:
			row[0] = '\t' * leading_tabs + row[0]
		process_row(row, width, options)
		rows.append(row)

	if not options:
		# Generate default options based on width
		options = [f"{{:>{w}}}" for w in width]

	adjust_options(options, width)
	format_str = gap.join(options)
	print_formatted_rows(rows, format_str, len(options), ostream)


def split_into_tables(istream: TextIO, multi_table: bool) -> list[list[str]]:
	"""Split input stream into tables based on multi-table option."""
	rx_split = get_tsv_format()
	tables = []
	current_table = []

	for line in istream:
		if multi_table and not rx_split.search(line):
			if current_table:
				tables.append(current_table)
				current_table = []
			tables.append([line])
		else:
			current_table.append(line)

	if current_table:
		tables.append(current_table)

	return tables


def tsv2txt(
	*format_options: str,
	istream: TextIO = sys.stdin,
	ostream: TextIO = sys.stdout,
	multi_table: bool = False,
	gap: str | int = 2,
	tabs: bool = False,
) -> None:
	"""
	Convert TSV (Tab-Separated Values) to formatted text.
	Supports multiple tables in input with the -m option.
	"""
	try:
		gap = int(gap)
		gap = " " * gap
	except ValueError:
		pass

	if tabs and gap[-1] == " ":
		gap = gap[:-1] + "\t"
	elif tabs:
		gap += "\t"

	options = Options(multi_table=multi_table, gap=gap, format_options=list(format_options))

	for i, opt in enumerate(options.format_options):
		if not opt:
			opt = '-'
		if not opt[-1].isalpha():
			opt += 'f' if '.' in opt else 's'
		options.format_options[i] = f'{{:{opt}}}'

	tables = split_into_tables(istream, options.multi_table)
	for table in tables:
		process_table(table, options.gap, options.format_options, ostream)


def setup_args(arg):
	"""Set up the command-line arguments."""
	arg("-m", "--multi-table", help="Support multiple tables in input", action="store_true")
	arg("-g", "--gap", help="Set gap between columns, either a string, or number of spaces")
	arg("-t", "--tabs", help="Hybrid format, spaced-out TSV: gap=\" \t\", edit with tabstop=1", action="store_true")
	arg("format_options", nargs="*", help="Format options for columns")


if __name__ == "__main__":
	main.go(tsv2txt, setup_args)
