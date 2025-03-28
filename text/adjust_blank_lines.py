#!/usr/bin/env python3-allemande
# adjust-blank-lines: Adjust blank lines in a text file

# This tool takes an input file or standard input, removes extra blank lines, and corrects the indentation for consecutive non-empty lines.

import argparse
import sys
import logging
import tempfile
import shutil


def collect_consecutive_blank_lines_and_comments(input_stream, comment_prefix=None):
	collected_lines = []
	stripped = ""
	while True:
		line = input_stream.readline()
		if not line:
			break
		logging.debug("Processing line: %s", line)
		line = line.rstrip('\r\n')
		stripped = line.strip()
		if comment_prefix and stripped.startswith(comment_prefix):
			stripped = ""
		if not stripped:
			break
		collected_lines.append(line)
	return collected_lines, line


def write_padded_lines(output_stream, indent_str, collected_lines):
	for line in collected_lines:
		output_stream.write(indent_str + line + '\n')


def adjust_blank_lines(input_stream, output_stream, python_style=False, comment_prefix=None):
	# TODO skip comments
	prev_line = ''
	prev_indent_str = ''
	for line in input_stream:
		line = line.rstrip('\r\n')
		logging.debug("Processing line: %s", line)
		stripped = line.strip()
		if not stripped:
			collected_lines, next_line = collect_consecutive_blank_lines_and_comments(input_stream, comment_prefix)
			next_indent_str = next_line[:len(next_line) - len(next_line.lstrip())]

			if python_style:
				indent_str = next_indent_str
			else:
				indent_str = max(prev_indent_str, next_indent_str, key=len)

			indent_str = max(prev_indent_str, next_indent_str, key=len)
			write_padded_lines(output_stream, indent_str, collected_lines)

			if next_line:
				output_stream.write(next_line + '\n')
			prev_indent_str = next_indent_str
		else:
			output_stream.write(line + '\n')
			prev_line = line
			prev_indent_str = line[:len(line) - len(stripped)]


def main():
	parser = argparse.ArgumentParser(description="Adjust blank lines in a text file.")
	parser.add_argument("--debug", action="store_true", help="Enable debug logging")
	parser.add_argument("--python", action="store_true", dest="python_style", help="Use Python style indentation")
	parser.add_argument("--comment", action="store_true", dest="comment_prefix", help="Comment prefix, e.g. # or ;")
	args = parser.parse_args()

	args = parser.parse_args()

	if args.debug:
		logging.basicConfig(level=logging.DEBUG)

	adjust_blank_lines(sys.stdin, sys.stdout, args.python_style, args.comment_prefix)

	logging.debug("Done")


if __name__ == "__main__":
	main()
