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

	def add_heading(section, heading_override=None):
		nonlocal key, heading, heading_lc, sub_heading, sub_heading_lc, data
		heading = section[2:].strip()
		detail = ""

		if ':' in heading:
			heading, detail = heading.split(':')
			detail = detail.strip()

		heading_lc = heading.lower()

		key = heading_override or heading_lc

		data[key] = { "heading": heading, "sections": [] }

		if detail:
			data[key]["detail"] = detail

		sub_heading = ""
		sub_heading_lc = ""
		key = heading_override or heading_lc

	def add_sub_heading(section):
		nonlocal key, sub_heading, sub_heading_lc, data, heading_lc
		sub_heading = section[3:].strip()
		sub_heading_lc = sub_heading.lower()
		data[key or heading_lc]["sections"].append({ "sub_heading": sub_heading, "content": "" })

	sub_heading = ""
	key = ""

	for section in sections:
		section = section.strip()
		if not section:
			continue

		# heading / starting section
		if section.startswith("# "):
			add_heading(section, key)

		elif section.startswith('## '):
			add_heading(section)

		# sub heading / sub section
		elif section.startswith('### '):
			add_sub_heading(section)

		# content
		else:
			content = section.strip() + '\n\n'
			if not heading:
				add_heading('## BLANK')
			if not sub_heading:
				add_sub_heading('### BLANK')
			if not data[key]["sections"]:
				add_sub_heading('### BLANK')
			data[key]["sections"][-1]["content"] += content

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
	logger.warning("replace_tags data: %s", json.dumps(list(data.keys()), indent=4))
	logger.warning("replace_tags map_contact_tags: %s", json.dumps(list(map_contact_tags.keys()), indent=4))
	def quote(text, quoted):
		logger.warning("quote text: %r, quoted: %r", text, quoted)
		if isinstance(text, dict):
			text = text["TEXT"]
		test = text or ""
		text = text.strip()
		if quoted:
			return f'"{text}"'
		return text
	def replace_tag(match):
		matched = match.group(0)
		quoted = matched.startswith('"') and matched.endswith('"')
		logger.warning("replace_tag matched: %r, quoted: %r", matched, quoted)
		tag = match.group(1) or match.group(2)
		tag = tag.upper()
		logger.warning("looking for tag %r", tag)
		if tag in data:
			logger.warning("tag in data: %r, data: %r", tag, data)
			if isinstance(data[tag], list):
				return quote(data[tag][0], quoted)
			return quote(data[tag], quoted)
		elif tag in map_contact_tags:
			logger.warning("tag in map_contact_tags data: %r, data: %r", tag, map_contact_tags)
			tag2 = map_contact_tags[tag]
			if tag2 in data:
				markdown_link = data[tag2][0]["TEXT"]
				link = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'\2', markdown_link)
				if re.search(r'[][]', link):
					logger.warning("link has square brackets: %r", link)
					link = re.sub(r'[][]', '', link)
				link = link.strip()
				if not link or link == "Unknown" or link == "N/A":
					link = ""
				return quote(link, quoted)
			return quote("", quoted)
		else:
			logger.warning("Tag not found: %s", tag)
			logger.warning("replace_tags data: %s", json.dumps(data, indent=4)) # list(data.keys()), indent=4))
			logger.warning("replace_tags map_contact_tags: %s", json.dumps(map_contact_tags, indent=4)) #
			return quote("", quoted)
	def replace_tag_debug(match):
		rv = replace_tag(match)
		logger.warning("replace_tag_debug match: %r, rv: %r", match, rv)
		return rv
	logger.warning("replace_tags text: %r, %r %r", r'\[([A-Z_]+)\]|"#([A-Z_]+)"', replace_tag_debug, text)
	text = re.sub(r'\[([A-Z_]+)\]|"#([A-Z_]+)"', replace_tag_debug, text)
	return text

def replace_tags_debug(text, data, map_contact_tags):
    rv = replace_tags(text, data, map_contact_tags)
    # logger.warning("replace_tags_debug text: %r, data: %r, map_contact_tags: %r, rv: %r", text, data, map_contact_tags, rv)
    return rv

def fill_template(data1, template_file, address):
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
	logger.debug(json.dumps(data1, indent=4))

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

	single_tags = ["INTRO_TITLE", "INTRO_TEXT", "ADDRESS"]
	main_sections = ["SEE", "DO", "LEARN", "TRAVEL", "BE_AWARE", "IN_THE_AREA", "LOCAL_GROUPS", "EAT_AND_DRINK", "ACCESSIBILITY", "RECAP"]

	main_sections_map = {
		"SEE": "See",
		"DO": "Do",
		"LEARN": "Learn",
		"TRAVEL": "Travel",
		"BE_AWARE": "Be Aware",
		"IN_THE_AREA": "In the Area",
		"LOCAL_GROUPS": "Local Groups",
		"EAT_AND_DRINK": "Eat & Drink",
		"ACCESSIBILITY": "Accessibility",
		"RECAP": "Recap",
	}

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
		"ADDRESS": address,
	}

	for heading in headings[1:]:
		heading_uc = heading.upper().replace(' ', '_')
		data[heading_uc + "_SUBHEADING"] = data1[heading]['heading']
		data[heading_uc] = []
		for section in data1[heading]['sections']:
			section_data = {
				"SUBHEADING": section['sub_heading'],
				"TEXT": section['content'],
			}
			data[heading_uc].append(section_data)

	# pretty print data for debugging

	logger.debug(json.dumps(data, indent=4))

	# process template one line at a time

	out_lines = []

	for line in template.split('\n'):
		tags = re.findall(r'\[([A-Z_]+)\]', line)
		# any multi tags?
		multi_tags = [tag for tag in tags if tag in main_sections]
		if not multi_tags:
			line = replace_tags_debug(line, data, map_contact_tags)
			out_lines.append(line)
		else:
			main_section = multi_tags[0].lower()
			main_section_uc = main_section.upper()
			sections = data.get(main_section_uc, [])

			first = True
			for section in sections:
				line2 = line
				tag_sub_heading = main_section_uc + "_SUBHEADING"
				tag_text = main_section_uc + "_TEXT"
				sub_heading = section['SUBHEADING']
				if sub_heading == "BLANK":
					sub_heading = ""
				text = section['TEXT']
				section_info = {
					tag_sub_heading: sub_heading,
					tag_text: text,
					"ADDRESS": address,
				}
				if first:
					section_info[main_section_uc] = main_sections_map[main_section_uc]
					first = False
				else:
					section_info[main_section_uc] = ""

				# section_info.update(data)
				line2 = replace_tags_debug(line2, section_info, map_contact_tags)
				out_lines.append(line2)

	return '\n'.join(out_lines) + '\n'

def place_md_to_wordpress(file=sys.stdin, template_file="template/tourism.txt", address=""):
	""" Place markdown text into Wordpress template. """
	text = file.read()
	data = read_markdown(text)
	page = fill_template(data, template_file, address=address)
	return page

if __name__ == "__main__":
	argh.dispatch_command(place_md_to_wordpress)
