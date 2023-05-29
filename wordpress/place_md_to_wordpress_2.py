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
	""" Read markdown text and convert it into a sensible data structure. """

	data = {}
	sections = text.split('\n\n')
	heading = ""
	heading_lc = ""
	sub_heading = ""
	sub_heading_lc = ""

	def add_heading(section):
		nonlocal heading, heading_lc, sub_heading, sub_heading_lc, data
		heading = section[2:].strip()
		detail = ""

		if ':' in heading:
			heading, detail = heading.split(':')
			detail = detail.strip()

		heading_lc = heading.lower()

		data[heading_lc] = { "heading": heading, "sections": [] }

		if detail:
			data[heading_lc]["detail"] = detail

		sub_heading = ""
		sub_heading_lc = ""

	def add_sub_heading(section):
		nonlocal sub_heading, sub_heading_lc, data
		sub_heading = section[3:].strip()
		sub_heading_lc = sub_heading.lower()
		data[heading_lc]["sections"].append({ "sub_heading": sub_heading, "content": "" })

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
			if not data[heading_lc]["sections"]:
				add_sub_heading('### Introduction')
			data[heading_lc]["sections"][-1]["content"] += content

	return data

def test_read_markdown():
	""" Test read_markdown() function. """
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

	data = read_markdown(markdown_text)
	# logger.warning(json.dumps(data, indent=4))
	assert data['inverloch']['heading'] == "Inverloch"
	assert data['inverloch']['detail'] == "Victoria's Coastal Gem"
	assert data['see']['sections'][0]['sub_heading'] == "Bunurong Coastal Drive"
	assert data['see']['sections'][0]['content'].startswith("Feast your eyes upon the breathtaking views...")
	assert data['do']['sections'][0]['sub_heading'] == "Adventures on the Water"
	assert data['do']['sections'][0]['content'].startswith("Whether you're a seasoned water sports enthusiast...")
	assert data['learn']['sections'][0]['sub_heading'] == "History and Dinosaurs"
	assert data['learn']['sections'][0]['content'].startswith("Inverloch was once a bustling port...")

def replace_tags(text, data, map_contact_tags):
	""" Replace tags in text with data. """
	logger.debug("replace_tags data: %s", json.dumps(list(data.keys()), indent=4))
	logger.debug("replace_tags map_contact_tags: %s", json.dumps(list(map_contact_tags.keys()), indent=4))
	def quote(text, quoted):
		if quoted:
			return f'"{text}"'
		return text
	def replace_tag(match):
		matched = match.group(0)
		quoted = matched.startswith('"') and matched.endswith('"')
		tag = match.group(1) or match.group(2)
		tag = tag.upper()
		if tag in data:
			logger.debug("tag: %r, data: %r", tag, data[tag])
			if isinstance(data[tag], list):
				return quote(data[tag][0]["TEXT"], quoted)
			return quote(data[tag], quoted)
		elif tag in map_contact_tags:
			tag2 = map_contact_tags[tag]
			if tag2 in data:
				markdown_link = data[tag2][0]["TEXT"]
				link = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'\2', markdown_link)
				return quote(link, quoted)
		else:
			logger.debug("Tag not found: %s", tag)
			return quote("", quoted)
	logger.debug("replace_tags text: %r, %r %r", r'\[([A-Z_]+)\]|"#([A-Z_]+)"', replace_tag, text)
	text = re.sub(r'\[([A-Z_]+)\]|"#([A-Z_]+)"', replace_tag, text)
	return text

def fill_template(data1, template_file):
	""" Fill template with data. """
	template = open(template_file).read()

#	[INTRO_TITLE]
#	[INTRO_TEXT]
#	[SEE_SUBHEADING]
#	[SEE_TEXT]
#	[DO_SUBHEADING]
#	[DO_TEXT]
#	[LEARN_SUBHEADING]
#	[LEARN_TEXT]
#	[TRAVEL_SUBHEADING]
#	[TRAVEL_TEXT]
#	[AWARE_SUBHEADING]
#	[AREA_SUBHEADING]
#	[LOCALGROUPS_SUBHEADING]
#	[LOCALGROUPS_TEXT]
#	[EATANDDRINK_SUBHEADING]
#	[EATANDDRINK_TEXT]
#	[AMENITIES_SUBHEADING]
#	[AMENITIES_TEXT]
#	[RECAP_SUBHEADING]
#	[RECAP_TEXT]

	headings = list(data1.keys())
	first_heading = headings[0]

	# pretty print data1 for debugging
	# logger.warning(json.dumps(data1, indent=4))

	# change data1 structure to match template

	# "address": {
	#        "heading": "Address",
	#        "sections": [
	#            {
	#                "sub_heading": "Introduction",
	#                "content": "Inverloch, Victoria, Australia\n\n"
	#            }
	#        ]
	#    }

	single_tags = ["INTRO_TITLE", "INTRO_TEXT"]
	main_sections = ["SEE", "DO", "LEARN", "TRAVEL", "AWARE", "AREA", "LOCALGROUPS", "EATANDDRINK", "AMENITIES", "RECAP"]

	map_contact_tags = {
		"FACEBOOK_LINK": "FACEBOOK",
		"INSTAGRAM_LINK": "INSTAGRAM",
		"LINKEDIN_LINK": "LINKEDIN",
		"TWITTER_LINK": "TWITTER",
		"VIMEO_LINK": "VIMEO",
		"YOUTUBE_LINK": "YOUTUBE",
		"EMAIL_LINK": "EMAIL",
		"PHONE_LINK": "PHONE_NUMBER",
	}

	single_tags += map_contact_tags.values()

	data = {
		"INTRO_TITLE": data1[first_heading]['heading'] + (": " + data1[first_heading]['detail'] if 'detail' in data1[first_heading] else ""),
		"INTRO_TEXT": data1[first_heading]['sections'][0]['content'],
	}

	for heading in headings[1:]:
		heading_uc = heading.upper().replace(' ', '_')
		data[heading_uc + "_HEADING"] = data1[heading]['heading']
		data[heading_uc] = []
		for section in data1[heading]['sections']:
			section_data = {
				"SUBHEADING": section['sub_heading'],
				"TEXT": section['content'],
			}
			data[heading_uc].append(section_data)

	# pretty print data for debugging

	# logger.warning(json.dumps(data, indent=4))

	# process template one line at a time

	out_lines = []

	for line in template.split('\n'):
		tags = re.findall(r'\[([A-Z_]+)\]', line)
		# any multi tags?
		multi_tags = [tag for tag in tags if tag in main_sections]
		if not multi_tags:
			line = replace_tags(line, data, map_contact_tags)
			out_lines.append(line)
		else:
			main_section = multi_tags[0].split('_')[0].lower()
			main_section_uc = main_section.upper()
			sections = data[main_section_uc]

			for section in sections:
				line2 = line
				tag_sub_heading = main_section_uc + "_SUBHEADING"
				tag_text = main_section_uc # + "_TEXT"
				sub_heading = section['SUBHEADING']
				text = section['TEXT']
				section_info = {
					tag_sub_heading: sub_heading,
					tag_text: text,
				}
				# section_info.update(data)
				line2 = replace_tags(line2, section_info, map_contact_tags)
				out_lines.append(line2)

	return '\n'.join(out_lines) + '\n'

def place_md_to_wordpress(file=sys.stdin, template_file="template/tourism.txt"):
	""" Place markdown text into Wordpress template. """
	text = file.read()
	data = read_markdown(text)
	page = fill_template(data, template_file)
	return page

if __name__ == "__main__":
	argh.dispatch_command(place_md_to_wordpress)
