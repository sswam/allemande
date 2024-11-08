#!/usr/bin/env python3-allemande

""" Split a file into multiple files on a given delimiter. """

# This tool takes one or more input files and splits each file into multiple
# output files based on a given delimiter. The new files are named after the
# input file and numbered in ascending order.


import os
import sys
import argparse
import logging
from typing import List, TextIO, Optional
import re
from enum import Enum
from math import inf
from tempfile import TemporaryDirectory
import io

from pytest import LogCaptureFixture


logger = logging.getLogger(__name__)


class IncludeDelimiter(Enum):
	""" What to do with the delimiter. """
	NONE = "none"
	START = "start"
	END = "end"
	BOTH = "both"


def get_file_size(file: TextIO) -> Optional[int]:
	""" Get the size of a file. """
	try:
		return os.fstat(file.fileno()).st_size
	except OSError:
		return None


def split_file(input_file: TextIO, opts: argparse.Namespace) -> None:
	""" Split a file into multiple files on a given delimiter. """

	# get the output file prefix
	try:
		output_file_prefix = opts.o or input_file.name
	except AttributeError:
		output_file_prefix = "unknown"
	if output_file_prefix == "<stdin>":
		output_file_prefix = "stdin"

	basename, ext = os.path.splitext(output_file_prefix)
	basename += "-"

	input_size = get_file_size(input_file)

	if opts.regexp:
		delimiter_regexp = opts.d
	else:
		delimiter_regexp = re.escape(opts.d)

	delimiter_regexp = re.compile(delimiter_regexp, re.MULTILINE | re.DOTALL)

	include_delimiter = IncludeDelimiter[opts.i.upper()]

	# if we have a limit option, we may accumulate more than one section in each file
	# otherwise, we'll only accumulate one section per file
	if opts.c == inf and opts.l == inf and opts.s == inf and opts.n is None:
		opts.s = 1

	# TODO: ideally I would like to load the file a block at a time, without
	# blocking, i.e. load what's available and only block if we didn't read any
	# data. This would be good for gradual streaming input.

	# this is the block size we'll read from the file
	block_size = opts.block_size

	# this is the buffer we'll use to store the data we read from the file
	buffer = ""

	file_num = 0
	output_file = None
	output_file_chars = 0
	output_file_lines = 0
	output_file_sections = 0
	total_chars_written = 0

	def open_output_file(file_num: int) -> TextIO:
		output_file_name = f"{basename}{file_num|0:06}{ext}"
		return open(output_file_name, 'w', encoding="utf-8")

	def write_section(section: str) -> None:
		nonlocal output_file
		nonlocal file_num
		nonlocal output_file_chars
		nonlocal output_file_lines
		nonlocal output_file_sections
		nonlocal total_chars_written

		if not opts.empty and not section:
			return

		# should we go to the next file?

		go_to_next_file = False

		if opts.c != inf and output_file_chars + len(data_to_write) > opts.c:
			go_to_next_file = True
		elif opts.l != inf and output_file_lines + len(data_to_write.splitlines()) > opts.l:
			go_to_next_file = True
		elif opts.s != inf and output_file_sections + 1 > opts.s:
			go_to_next_file = True
		elif opts.n is not None and input_size is not None:
			n_files_remaining = opts.n - file_num + 1
			n_chars_remaining = input_size - total_chars_written
			if output_file_chars + len(data_to_write) > n_chars_remaining / n_files_remaining:
				go_to_next_file = True

		# go to the next file if necessary
		if go_to_next_file and output_file:
			output_file.close()
			output_file = None

		if not output_file:
			file_num += 1
			output_file = open_output_file(file_num)
			output_file_chars = 0
			output_file_lines = 0
			output_file_sections = 0

		output_file.write(section)
		output_file_chars += len(section)
		output_file_lines += len(section.splitlines())
		output_file_sections += 1

	# read loop
	while True:
		# read a block of data from the file
		data = input_file.read(block_size)

		# if we didn't read any data, we output the remaining buffer and exit
		if not data:
			data_to_write = buffer
			buffer = ""
			write_section(data_to_write)
			break

		# add the data to the buffer
		buffer += data

		# look for the delimiter in the buffer
		# we don't want to match the delimiter at the start of the buffer
		while match := re.search(delimiter_regexp, buffer[1:]):
			delimiter = match.group(0) if match else None

			logger.debug("delimiter: %s", delimiter)

			# if we didn't find the delimiter, we'll just keep reading
			if not delimiter:
				continue

			# Split the buffer on the delimiter
			before_delimiter, _delimiter, buffer2 = buffer[1:].partition(delimiter)
			before_delimiter = buffer[0] + before_delimiter

			assert _delimiter == delimiter

			logger.debug("before_delimiter: %s", before_delimiter)
			logger.debug("buffer2: %s", buffer2)

			# what to do with the delimiter
			data_to_write = before_delimiter
			if include_delimiter in (IncludeDelimiter.END, IncludeDelimiter.BOTH):
				logger.debug("case 1: include_delimiter: %s", include_delimiter)
				data_to_write += delimiter
			if include_delimiter in (IncludeDelimiter.START, IncludeDelimiter.BOTH):
				logger.debug("case 2: include_delimiter: %s", include_delimiter)
				buffer2 = delimiter + buffer2

			logger.debug("data_to_write: %s", data_to_write)

			# write the data to the output file
			write_section(data_to_write)

			buffer = buffer2


def test_split_file(caplog: LogCaptureFixture) -> None:
	""" Test split_file """
	def test_split_file_helper(input_data: str, expected_output: List[str], opts: argparse.Namespace) -> None:
		cwd = os.getcwd()

		# do this in a temporary directory
		with TemporaryDirectory() as tmpdir:
			os.chdir(tmpdir)

			input_file = io.StringIO(input_data)
			split_file(input_file, opts)
			output = []
			for file_num in range(1, 100):
				try:
					file_name = f"unknown.{file_num}"
					with open(file_name, 'r', encoding="utf-8") as output_file:
						output.append(output_file.read())
				except FileNotFoundError:
					break

			os.chdir(cwd)

		assert output == expected_output

	caplog.set_level(logging.DEBUG)

	opts = argparse.Namespace()
	opts.b = 1024
	opts.c = opts.l = opts.s = inf
	opts.n = None
	opts.regexp = False
	opts.empty = False

	opts.i = "end"
	opts.d = "."
	test_split_file_helper("This is a test.", ["This is a test."], opts)

	opts.d = " "
	test_split_file_helper("This is a test.", ["This ", "is ", "a ", "test."], opts)

	# test splitting on blank lines
	opts.regexp = True
	opts.d = r'^\n'
	opts.i = "none"
	test_split_file_helper("This is a test.\n\nThis is another test.", ["This is a test.", "This is another test."], opts)


def split_files(input_files: List[str], opts: argparse.Namespace) -> None:
	""" Split files based on delimiter """
	for file_name in input_files:
		logger.info("Splitting file %s...", file_name)
		with open(file_name, 'r', encoding="utf-8") as input_file:
			split_file(input_file, opts)


def main() -> None:
	""" Main entry point of the app """
	parser = argparse.ArgumentParser(description="Split files based on delimiter.")

	input_group = parser.add_argument_group("input", "Input files and delimiter options")
	input_group.add_argument("files", nargs="*", help="Files to split.")
	input_group.add_argument("-d", default="\n\n", help="Delimiter to split files on (default is a blank line).")
	input_group.add_argument("-r", "--regexp", action="store_true", help="The delimiter is a regular expression; otherwise, it's a string.")
	input_group.add_argument("-b", "--block-size", type=int, default=1024, help="Block size to read from the input file (default 1024).")

	output_group = parser.add_argument_group("output", "Output file options")
	include_delimiter_choices = [str(x).lower() for x in IncludeDelimiter.__members__]
	output_group.add_argument("-i", choices=include_delimiter_choices, default="end", help="Include the delimiters in the output files at the specified position (default 'end').")
	output_group.add_argument("-o", default=None, help="Output file prefix (default derived from input file name).")
	output_group.add_argument("--empty", action="store_true", help="Output empty files, including the last file.")

	limit_group = parser.add_argument_group("limit", "Limit the split files by size, lines, or sections")
	limit_group.add_argument("-c", type=int, default=inf, help="Maximum number of chars per file.")
	limit_group.add_argument("-l", type=int, default=inf, help="Maximum number of lines per file.")
	limit_group.add_argument("-s", type=int, default=inf, help="Maximum number of sections per file.")
	limit_group.add_argument("-n", type=int, default=None, help="Desired number of files to split into.")
	limit_group.add_argument("--size", type=int, default=inf, help="Estimated size of the input file, for pipes.")

	logging_group = parser.add_argument_group("logging", "Logging options")
	logging_group.add_argument("--debug", action="store_true", help="Enable debug logging.")

	opts = parser.parse_args()
	args = opts.files

	logging.basicConfig(level=logging.DEBUG if opts.debug else logging.INFO)

	logger.debug("opts: %s", opts)

	if args:
		split_files(args, opts)
	else:
		logger.info("Splitting stdin...")
		split_file(sys.stdin, opts)

if __name__ == '__main__':
	main()
