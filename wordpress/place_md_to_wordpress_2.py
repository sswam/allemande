#!/usr/bin/env python3
"""
markdown_to_structure.py: Read markdown text and convert it into a sensible
data structure with keys like title, introduction, see_subheading, see, etc.
"""

import sys
import re
import argh
import logging
import json

logger = logging.getLogger(__name__)

def read_markdown(text):
	"""
	Read markdown text and convert it into a sensible data structure.
	"""

	data_structure = {}
	sections = text.split('\n\n')
	heading = ""
	heading_lc = ""
	sub_heading = ""
	sub_heading_lc = ""

	def add_heading(section):
		nonlocal heading, heading_lc, sub_heading, sub_heading_lc, data_structure
		heading = section[2:].strip()
		detail = ""
	
		if ':' in heading:
			heading, detail = heading.split(':')
			detail = detail.strip()

		heading_lc = heading.lower()

		data_structure[heading_lc] = { "heading": heading, "sections": [] }

		if detail:
			data_structure[heading_lc]["detail"] = detail

		sub_heading = ""
		sub_heading_lc = ""

	def add_sub_heading(section):
		nonlocal sub_heading, sub_heading_lc, data_structure
		sub_heading = section[3:].strip()
		sub_heading_lc = sub_heading.lower()
		data_structure[heading_lc]["sections"].append({ "sub_heading": sub_heading, "content": "" })

	sub_heading = ""

	for section in sections:
		section = section.strip()
		if not section:
			continue

		# heading / starting section
		if section.startswith('## '):
			add_heading(section)

		# sub heading / sub section
		elif section.startswith('### '):
			add_sub_heading(section)

		# content
		else:
			content = section.strip() + '\n\n'
			if not heading:
				add_heading('## Introduction')
			if not sub_heading:
				add_sub_heading('### Introduction')
			if not data_structure[heading_lc]["sections"]:
				add_sub_heading('### Introduction')
			data_structure[heading_lc]["sections"][-1]["content"] += content

	return data_structure

def test_read_markdown():
	markdown_text = '''## Inverloch

## Inverloch: Victoria's Coastal Gem

As you make your way down the Bass Highway...

## See

### Bunurong Coastal Drive

Feast your eyes upon the breathtaking views...

## Do

### Adventures on the Water

Whether you're a seasoned water sports enthusiast...

## Learn

### History and Dinosaurs

Inverloch was once a bustling port...'''

	data_structure = read_markdown(markdown_text)
	logger.warning(json.dumps(data_structure, indent=4))
	assert data_structure['inverloch']['heading'] == "Inverloch"
	assert data_structure['inverloch']['detail'] == "Victoria's Coastal Gem"
	assert data_structure['see']['sections'][0]['sub_heading'] == "Bunurong Coastal Drive"
	assert data_structure['see']['sections'][0]['content'].startswith("Feast your eyes upon the breathtaking views...")
	assert data_structure['do']['sections'][0]['sub_heading'] == "Adventures on the Water"
	assert data_structure['do']['sections'][0]['content'].startswith("Whether you're a seasoned water sports enthusiast...")
	assert data_structure['learn']['sections'][0]['sub_heading'] == "History and Dinosaurs"
	assert data_structure['learn']['sections'][0]['content'].startswith("Inverloch was once a bustling port...")

def place_md_to_wordpress(file=sys.stdin):
	text = file.read()
	data_structure = read_markdown(text)
	json.dump(data_structure, sys.stdout, indent=4)
	return data_structure

if __name__ == "__main__":
	argh.dispatch_command(place_md_to_wordpress)
