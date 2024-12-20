#!/usr/bin/env python3-allemande
""" tab: Convert spaces to tabs """

from sys import stdin, stdout
import re
import logging
import argparse
from typing import IO
from os.path import commonprefix

import argh

from ally import main

logger = logging.getLogger(__name__)


def identity(x):
	""" identity function """
	return x

def filter_non_blank_lines(lines):
	""" return only non-blank lines """
	return filter(identity, lines)

def rstrip_lines(lines):
	""" strip trailing whitespace from lines """
	return map(str.rstrip, lines)

def get_line_indent(line):
	""" return the indent of a line """
	indent = re.match(r'^\s*', line).group(0)
	return indent

def get_common_indent(lines):
	""" return the common indent of the lines """
	common_prefix = commonprefix(list(lines))
	indent = get_line_indent(common_prefix)
	return indent

def strip_common_indent(lines):
	""" if all of the lines are indented, then strip the common indent """
	lines = list(lines)
	non_blank_lines = list(filter_non_blank_lines(lines))
	common_indent = get_common_indent(non_blank_lines)
	if common_indent:
		n = len(common_indent)
		lines = [line[n:] for line in lines]
	return lines

def test_strip_common_indent():
	""" test strip_common_indent """
	assert strip_common_indent(['foo', 'bar', 'baz']) == ['foo', 'bar', 'baz']
	assert strip_common_indent(['\tfoo', '\tbar', '\tbaz']) == ['foo', 'bar', 'baz']
	assert strip_common_indent(['\tfoo', '  bar', '\tbaz']) == ['\tfoo', '  bar', '\tbaz']

def get_indented_lines(lines):
	""" return only indented lines """
	return filter(get_line_indent, lines)

def get_tab_string(lines):
	""" return the indent unit string """
	indented_lines = get_indented_lines(lines)
	common_indent = get_common_indent(indented_lines)
	return common_indent

def replace_indentation(line, tab_old, tab):
	""" replace the indentation of a line """
	# check if first char is a whitespace
	indent = get_line_indent(line)
	if not indent:
		return line
	indent_len = len(indent) // len(tab_old)
	if indent != tab_old * indent_len:
		logging.info("Inconsistent indentation: " + repr(line))
		return line
	return tab * indent_len + line[len(indent):]

def add_newline(lines):
	""" add a newlines to the end of the lines """
	return map(lambda line: line + "\n", lines)

def fix_indentation_list(lines, tab):
	""" fix the indentation of the lines """

	lines = rstrip_lines(lines)
	lines = strip_common_indent(lines)

	tab_old = get_tab_string(lines)

	if not tab_old:
		logging.debug("No indentation found")
	elif tab_old != tab:
		lines = map(lambda line: replace_indentation(line, tab_old, tab), lines)

	lines = add_newline(lines)

	return lines

@argh.arg('-c', help='character to use for tab')
def fix_indentation(inp: IO[str]=stdin, out: IO[str]=stdout, n=1, c='\t', tab=None):
	""" fix the indentation of a file """
	if not tab:
		tab = n * c
	# input_lines = inp.readlines()
	fixed_lines = list(fix_indentation_list(inp, tab))
	out.writelines(fixed_lines)

if __name__ == '__main__':
	main.run(fix_indentation)
