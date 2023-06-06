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
import markdown

logger = logging.getLogger(__name__)

EMPTY_TEXT = {
	"SEE": "Nothing to see here... 👷",
	"DO": "Nothing to do here... 👷",
	"LEARN": "Nothing to learn here... 👷",
	"EAT_AND_DRINK": "Nothing to eat or drink here... 👷",
	"GETTING_THERE": "No way to get there... 👷",
	"STAY": "No accommodation here... 👷",
	"IN_THE_AREA": "Nothing in the area... 👷",
	"EVENTS": "No events here... 👷",
	"LOCAL_GROUPS": "No local groups here... 👷",
	"ACCESSIBILITY": "No accessibility information... 👷",
	"WARNINGS": "It's safe here...? 👷",
	"RECAP": "Nothing to recap here... 👷",
}

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
				add_heading('## KILL')
			if not sub_heading:
				add_sub_heading('### KILL')
			if not data[key]["sections"]:
				add_sub_heading('### KILL')
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
#	logger.debug("replace_tags data: %s", json.dumps(list(data.keys()), indent=4))
#	logger.debug("replace_tags map_contact_tags: %s", json.dumps(list(map_contact_tags.keys()), indent=4))
	def quote(text, quoted):
		logger.debug("quote text: %r, quoted: %r", text, quoted)
		if isinstance(text, dict):
			text = text["TEXT"]
		text = text.strip()
		text = text or "KILL"
		if quoted:
			return f'"{text}"'
		try:
			html_content = markdown.markdown(text)
		except Exception as e:
			logger.error("markdown error: %r", e)
			html_content = text
		return html_content
	
	def replace_tag(match):
		matched = match.group(0)
		quoted = matched.startswith('"') and matched.endswith('"')
		logger.debug("replace_tag matched: %r, quoted: %r", matched, quoted)
		tag = match.group(1) or match.group(2) or match.group(3)
		keep_unknown = bool(match.group(3))
		tag = tag.upper()
		logger.debug("looking for tag %r", tag)

		detail = False
		index = 0
		logger.debug("tag: %r", tag)
		if tag.endswith(("_SUBHEADING", "_TEXT")):
			detail = True
		else:
			m = re.search(r"_(\d+)$", tag)
			if m:
				index = int(m.group(1)) - 1
				tag = re.sub(r"_(\d+)$", "", tag)
				detail = True

		logger.debug("tag: %r, index: %r, detail: %r", tag, index, detail)

#		if tag not in ("SEE_SUBHEADING", "SEE_TEXT", "SEE_SUBHEADING_2", "SEE_TEXT_2"):
#			return quote("", quoted)

		# NOTE: HACK
		if detail:
			for suffix in "SUBHEADING", "TEXT", "SUBHEADING_2", "TEXT_2":
				if not tag.endswith("_"+suffix):
					continue
				logger.debug("tag ends with %r", suffix)
				section = tag[:-len(suffix)-1]
				sections = data.get(section)
				if not sections:
					logger.debug("section not found: %r", section)
					return quote("", quoted)
				if index < len(sections):
					sec = sections[index]
					value = sec[suffix]
					return quote(value, quoted)
				elif index > 0:
					return quote("KILL", quoted)
				else:
					return guote(EMPTY_TEXT.get(section, "KILL"))

		if tag in data:
			logger.debug("tag in data: %r, data: %r", tag, data)
			if isinstance(data[tag], list):
				return quote(data[tag][0], quoted)
			return quote(data[tag], quoted)
		elif tag in map_contact_tags:
			tag2 = map_contact_tags[tag]
			logger.debug("tag in map_contact_tags tag: %r, data: %r, tag2: %r", tag, data, tag2)
			if tag2 in data:
				markdown_link = data[tag2][0]["TEXT"]
				link = re.sub(r'\[([^\]]+)\]\(([^\)]+)\)', r'\2', markdown_link)
				if re.search(r'[][]', link):
					logger.debug("link has square brackets: %r", link)
					link = re.sub(r'[][]', '', link)
				link = link.strip()
				if not link or link == "Unknown" or link == "N/A":
					link = ""
				return quote(link, quoted)
			return quote("", quoted)
		elif keep_unknown:
			logger.debug("Tag not found: %s, maybe it's a color?", tag)
			return match.group()
		else:
			logger.debug("Tag not found: %s, removing line", tag)
			# logger.debug("replace_tags data: %s", json.dumps(data, indent=4)) # list(data.keys()), indent=4))
			# logger.debug("replace_tags map_contact_tags: %s", json.dumps(map_contact_tags, indent=4))
			return quote("", quoted)

	def replace_tag_debug(match):
		matched = match.group(0)
		rv = replace_tag(match)
		if "YOUTUBE" in matched:
			logger.warning(f"replace_tag: matched={matched} rv={rv}")
#		logger.debug("replace_tag_debug match: %r, rv: %r", match, rv)
		return rv

	text = re.sub(r'https://www\.facebook\.com/insert-fb-page', '#social-facebook', text)

#	logger.debug("replace_tags text: %r, %r %r", r'\{([A-Z0-9_]+)\}|"#([A-Z0-9_]+)"', replace_tag_debug, text)
	text = re.sub(r'"\{([A-Z0-9_]+)\}"|\{([A-Z0-9_]+)\}|"#([a-z0-9-]+)"', replace_tag_debug, text)
	if "KILL" in text:
		logger.warning("killing line: %s", text)
		text = ""
	return text

def replace_tags_debug(text, data, map_contact_tags):
    rv = replace_tags(text, data, map_contact_tags)
#    logger.debug("replace_tags_debug text: %r, data: %r, map_contact_tags: %r, rv: %r", text, data, map_contact_tags, rv)
    return rv

def fill_template(data1, template, address):
	""" Fill template with data. """

	headings = list(data1.keys())
	first_heading = headings[0]

	# pretty print data1 for debugging into a file data1.json
	with open("data1.json", "w") as f:
		f.write(json.dumps(data1, indent=4))

	single_tags = ["INTRO_TITLE", "INTRO_TEXT", "ADDRESS"]
	main_sections = [ "SEE", "DO", "LEARN", "EAT_AND_DRINK", "GETTING_THERE", "STAY", "IN_THE_AREA", "EVENTS", "ACCESSIBILITY", "LOCAL_GROUPS", "WARNINGS", "RECAP" ]
	multi_tags_all = [f"{section}_SUBHEADING_2" for section in main_sections] + [f"{section}_TEXT_2" for section in main_sections]

	main_sections_map = {
		"SEE": "See",
		"DO": "Do",
		"LEARN": "Learn",
		"EAT_AND_DRINK": "Eat & Drink",
		"GETTING_THERE": "Getting There",
		"STAY": "Stay",
		"IN_THE_AREA": "In the Area",
		"EVENTS": "Events",
		"LOCAL_GROUPS": "Local Groups",
		"ACCESSIBILITY": "Accessibility",
		"WARNINGS": "Warnings",
		"RECAP": "Recap",
	}

	map_contact_tags = {
		"SOCIAL-FACEBOOK": "OFFICIAL_FACEBOOK_PAGE",
		"SOCIAL-INSTAGRAM": "OFFICIAL_INSTAGRAM_PAGE",
		"SOCIAL-LINKEDIN": "OFFICIAL_LINKEDIN_PAGE",
		"SOCIAL-TWITTER": "OFFICIAL_TWITTER_PAGE",
		"SOCIAL-VIMEO": "OFFICIAL_VIMEO_CHANNEL",
		"SOCIAL-YOUTUBE": "OFFICIAL_YOUTUBE_CHANNEL",
		"SOCIAL-EMAIL": "EMAIL",
		"SOCIAL-PHONE-NUMBER": "PHONE_NUMBER",
		"SOCIAL-BLOGGER": "BLOGGER",
		"SOCIAL-DEVIANTART": "DEVIANTART",
		"SOCIAL-DIGG": "DIGG",
		"SOCIAL-DISCORD": "DISCORD",
		"SOCIAL-DROPBOX": "DROPBOX",
		"SOCIAL-FLICKR": "FLICKR",
		"SOCIAL-PAYPAL": "PAYPAL",
		"SOCIAL-PHONE": "PHONE_NUMBER",
		"SOCIAL-PINTEREST": "PINTEREST",
		"SOCIAL-REDDIT": "REDDIT",
		"SOCIAL-RSS": "RSS",
		"SOCIAL-SKYPE": "SKYPE",
		"SOCIAL-SNAPCHAT": "SNAPCHAT",
		"SOCIAL-SOUNDCLOUD": "SOUNDCLOUD",
		"SOCIAL-SPOTIFY": "SPOTIFY",
		"SOCIAL-TEAMS": "TEAMS",
		"SOCIAL-TIKTOK": "TIKTOK",
		"SOCIAL-TUMBLR": "TUMBLR",
		"SOCIAL-TWITCH": "TWITCH",
		"SOCIAL-WECHAT": "WECHAT",
		"SOCIAL-WHATSAPP": "WHATSAPP",
		"SOCIAL-YAHOO": "YAHOO",
		"SOCIAL-YELP": "YELP",
	}

	single_tags += map_contact_tags.values()

	data = {
		"INTRO_TITLE": data1[first_heading]['heading'] + (": " + data1[first_heading]['detail'] if 'detail' in data1[first_heading] else ""),
		"INTRO": data1[first_heading]['sections'][0]['content'],
		"ADDRESS": address,
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

	# pretty print data1 for debugging into a file data1.json
	with open("data2.json", "w") as f:
		f.write(json.dumps(data, indent=4))

	# process template one line at a time

	out_lines = []

	line_iter = iter(template.split('\n'))
	while True:
		line = next(line_iter, None)

		if line is None:
			break

		if line.startswith("<!--"):
			# skip comment
			continue

		if line == "{":
			acc = ""
			while True:
				line = next(line_iter, None)
				if line is None:
					break
				if line == "}":
					line = acc
					break
				if acc:
					acc += "\n"
				acc += line

		tags = re.findall(r'\{([A-Z0-9_]+)\}', line)
		# any multi tags?
		multi_tags = [tag for tag in tags if tag in multi_tags_all]
		line = replace_tags_debug(line, data, map_contact_tags)
		out_lines.append(line)

#		if not multi_tags:
#			line = replace_tags_debug(line, data, map_contact_tags)
#			out_lines.append(line)
#		else:
#			main_section = multi_tags[0].lower().replace('_subheading_2', '').replace('_text_2', '')
#			# main_section = multi_tags[0].lower() #.replace('_subheading_2', '').replace('_text_2', '')
#			main_section_uc = main_section.upper()
#			sections = data.get(main_section_uc, [])
#			logger.warning("multi_tags: %r", multi_tags)
#			logger.warning("main_section: %r", main_section)
#			logger.warning("sections: %r", sections)
#
#			first = True
#			for section in sections:
#				logger.warning("section: %r", section)
#				line2 = line
#				tag_sub_heading = main_section_uc + "_SUBHEADING"
#				tag_text = main_section_uc + "_TEXT"
#				sub_heading = section['SUBHEADING']
#				if sub_heading == "BLANK":
#					sub_heading = ""
#				text = section['TEXT']
#				section_info = {
#					tag_sub_heading: sub_heading,
#					tag_text: text,
#					"ADDRESS": address,
#				}
#				if first:
#					section_info[main_section_uc] = main_sections_map[main_section_uc]
#					first = False
#				else:
#					section_info[main_section_uc] = ""
#
#				# section_info.update(data)
#				line2 = replace_tags_debug(line2, section_info, map_contact_tags)
#				out_lines.append(line2)

	return '\n'.join(out_lines) + '\n'


# TODO move to library

def slurp(pathname, errors="ignore"):
	""" Read file and return contents as string. """
	with open(pathname, 'r', errors=errors) as f:
		return f.read()


@argh.arg("--content_file", "-c", help="Markdown file to process.")
@argh.arg("--metadata_file", "-m", help="Metadata file to process.")
@argh.arg("--template_file", "-t", help="Template file to process.")
@argh.arg("--address", "-a", help="Address to use.")
def place_md_to_wordpress(content_file="content.md", metadata_file="metadata.md", template_file="template/tourism.txt", address=""):
	""" Place markdown text into Wordpress template. """
	# read content and metadata, from named files content_file and metadata_file
	content = read_markdown(slurp(content_file))
	metadata = read_markdown(slurp(metadata_file))
	template = slurp(template_file)
	data = {}
	data.update(content)
	data.update(metadata)
	page = fill_template(data, template, address=address)
	return page

if __name__ == "__main__":
	argh.dispatch_command(place_md_to_wordpress)
