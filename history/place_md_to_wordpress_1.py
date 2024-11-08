#!/usr/bin/env python3-allemande

import sys
import re
from pathlib import Path

import logging

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)

SCRIPT_DIR = Path(__file__).parent.resolve()
BLOCKS_DIR = SCRIPT_DIR / 'blocks'


def print_block(name):
	block_file = BLOCKS_DIR / name
	if not block_file.exists():
		raise Exception('Block file not found: ' + str(block_file))
	with block_file.open() as f:
		print(f.read(), end='')


inp = sys.stdin

rd_pushback = []

def rd(skip_blank=True):
	while True:
		if rd_pushback:
			line = rd_pushback.pop()
		else:
			line = inp.readline()
			if line == '':
				return None
			line = line.rstrip()
		if skip_blank and not line:
			continue
		return line


def unrd(line):
	rd_pushback.append(line)


def get_heading_info(heading):
	level = 0
	m = re.match(r"(#+)\s*", heading)
	if m:
		level = len(m.group(1))
		heading = re.sub(r"(#+)\s*", "", heading)
	return level, heading


def read_section():
	content = []

	# main heading

	heading = rd()
	if heading is None:
		return None, None, None, None, None

	level, heading = get_heading_info(heading)

	if level == 0:
		content.append(heading)
		heading = None

	# subheading

	subheading = rd()
	if subheading is None:
		return level, heading, 0, None, content

	level2, subheading = get_heading_info(subheading)

	if level2 == 0:
		content.append(subheading)
		subheading = None

	# content lines

	while True:
		line = rd()
		if line is None:
			break
		if re.match(r"(#+)\s*", line):
			unrd(line)
			break
		content.append(line)
	
	return level, heading, level2, subheading, content


def print_main_section(heading, content):
	print_block("main_" + str(len(content)))

	if heading is not None:
		print(heading)
		print("")

	for line in content:
		print(line)


def print_section(content):
	for paragraph in content:
		if paragraph is not None:
			print(paragraph)
			print("")


# main intro section

level, heading, level2, subheading, content = read_section()

if level is None:
	logger.warning("No main section found")
elif level != 1:
	logger.warning("Expected level 1 heading for main intro section, got: %r", level)

if level is not None:
	print_block("main_open")
	
	print_section([heading or ""])

	print_block("main_sep1")

	print_section(content)
	
	print_block("main_close")
	

# loop over each section

section = 1

while True:

	level, heading, level2, subheading, content = read_section()

	if level is None:
		break
	
	if level != 2:
		logger.warning("Expected level 2 heading for section, got: %r", level)
	
	if level2 != 3:
		logger.warning("Expected level 3 sub-heading for section, got: %r", level2)

	if section % 2 == 1:
		# odd number sections, heading on left
		
		print_block("section_left_open")
		
		print_section([heading or ""])
		
		print_block("section_left_sep1")

		print_section([subheading or ""])

		print_block("section_left_sep2")

		print_section(content)

		print_block("section_left_close")

	else:
		# even number sections, heading on right
	
		print_block("section_right_open")

		print_section([subheading or ""])

		print_block("section_right_sep1")

		print_section(content)

		print_block("section_right_sep2")
		
		print_section([heading or ""])
		
		print_block("section_right_close")

	section += 1


print_block("footer")
