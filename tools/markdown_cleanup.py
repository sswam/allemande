#!/usr/bin/env python3-allemande

# markdown-cleanup: A script to clean up markdown text, adding blank lines around lists

import sys
import argh
import re

def add_blank_lines_around_lists(markdown_text):
	""" Add blank lines around lists in markdown text """
	if markdown_text[-1] == '\n':
		markdown_text = markdown_text[:-1]

	lines = markdown_text.split('\n')
	output_lines = []

	in_list = False
	prev_blank = True

	for i, line in enumerate(lines):
		if not line:
			prev_blank = True
			output_lines.append(line)
			continue
		if re.match(r'^\s*[-*]\s+', line) or re.match(r'^\s*\d+\.\s+', line):
			if not in_list:
				output_lines.append('')
			in_list = True
		elif in_list and not prev_blank and i < len(lines)-1:
			in_list = False
			output_lines.append('')
		elif in_list:
			in_list = False

		output_lines.append(line)
		prev_blank = False

	return '\n'.join(output_lines)+'\n'

def main():
	""" Main function """
	markdown_text = sys.stdin.read()
	result = add_blank_lines_around_lists(markdown_text)
	sys.stdout.write(result)

def test():
	""" Test the function with some markdown text """
	markdown_text = '''This is some text.
- Item 1
- Item 2
This is more text.
1. Numbered item 1
2. Numbered item 2
'''
	output = add_blank_lines_around_lists(markdown_text)
	print(output)
	assert output == '''This is some text.

- Item 1
- Item 2

This is more text.

1. Numbered item 1
2. Numbered item 2
'''

if __name__ == '__main__':
	argh.dispatch_command(main)
