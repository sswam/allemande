#!/usr/bin/env python3

""" chat.py: Allemande chat file format library """

import sys
import itertools
import html
from pathlib import Path
import re
import logging

import argh
import markdown


logger = logging.getLogger(__name__)


class Singleton:
	def __init__(self, name):
		self.name = name
	def __repr__(self):
		return f"<{self.name}>"

USER_NARRATIVE = Singleton("Narrative")
USER_CONTINUED = Singleton("Continued")
ROOM_MAX_LENGTH = 100
ROOM_MAX_DEPTH = 10

# see: https://python-markdown.github.io/extensions/
MARKDOWN_EXTENSIONS = [
	'abbr',
	# 'attr_list',
	'def_list',
	'fenced_code',
	'footnotes',
	'md_in_html',
	'tables',
	'admonition',
	# 'codehilite',
	# 'legacy_attrs',
	# 'legacy_em',
	# 'meta',
	'nl2br',
	'sane_lists',
	# 'smarty',
	'toc',
	'wikilinks',
	'markdown_katex',
]

MARKDOWN_EXTENSION_CONFIGS = {
	'markdown_katex': {
#		'no_inline_svg': True, # fix for WeasyPrint
		'insert_fonts_css': True,
	},
}

def safe_join(base_dir: Path, path: Path) -> Path:
	""" Return a safe path under base_dir, or raise ValueError if the path is unsafe. """
	safe_path = base_dir.joinpath(path).resolve()
	if base_dir in safe_path.parents:
		return safe_path
	else:
		raise ValueError("Invalid or unsafe path provided: %r, %r" % (base_dir, path))

def sanitize_filename(f):
	""" Sanitize a filename, allowing most characters. """

	assert isinstance(f, str)
	assert "/" not in f

	# remove leading dots and whitespace:
	# don't want hidden files
	f = re.sub(r"^[.\s]+", "", f)

	# remove trailing dots and whitespace:
	# don't want confusion around file extensions
	f = re.sub(r"[.\s]+$", "", f)

	# squeeze whitespace
	f = re.sub(r"\s+", " ", f)

	return f


def sanitize_pathname(room):
	""" Sanitize a pathname, allowing most characters. """

	# split into parts
	parts = room.split("/")

	# sanitize each part
	parts = map(sanitize_filename, parts)

	# remove empty parts
	parts = list(filter(lambda x: x, parts))

	if not parts:
		raise HTTPException(status_code=400, detail="Please enter the name of a room.")

	if len(parts) > ROOM_MAX_DEPTH:
		raise HTTPException(status_code=400, detail=f"The room is too deeply nested, max {ROOM_MAX_DEPTH} parts.")

	# join back together
	room = "/".join(parts)

	if len(room) > ROOM_MAX_LENGTH:
		raise HTTPException(status_code=400, detail=f"The room name is too long, max {ROOM_MAX_LENGTH} characters.")

	# check for control characters
	if re.search(r"[\x00-\x1F\x7F]", room):
		raise HTTPException(status_code=400, detail="The room name cannot contain control characters.")

	return room


def split_message_line(line):
	""" Split a message line into user and content. """

	if not line.endswith("\n"):
		line += "\n"

	if "\t" in line:
		label, content = line.split("\t", 1)
	else:
		label = None
		content = line

	logger.debug("split_message_line line, label, content: %r, %r, %r", line, label, content)

	if label is None:
		user = USER_NARRATIVE
	elif label == "":
		user = USER_CONTINUED
	elif label.endswith(":"):
		user = label[:-1]
	else:
		logger.warning("Invalid label missing colon, in line: %s", line)
		user = USER_NARRATIVE
		content = label + "\t" + content

	return user, content


def lines_to_messages(lines):
	""" A generator to convert an iterable of lines to chat messages. """

	message = None

	lines = iter(lines)
	skipped_blank = 0

	while True:
		line = next(lines, None)
		if line is None:
			break

		if type(line) is bytes:
			line = line.decode("utf-8")

		# skip blank lines
		if line.rstrip("\r\n") == "":
			skipped_blank += 1
			continue

		user, content = split_message_line(line)

		# accumulate continued lines
		if message and user == USER_CONTINUED:
			message["content"] += "\n" * skipped_blank + content
			skipped_blank = 0
			continue

		if not message and user == USER_CONTINUED:
			logger.warning("Continued line with no previous incomplete message: %s", line)
			user = USER_NARRATIVE

		if message and user == USER_NARRATIVE and "user" not in message:
			message["content"] += "\n" * skipped_blank + content
			skipped_blank = 0
			continue

		# yield the previous message
		if message:
			logger.debug(message)
			yield message
			message = None

		# start a new message
		skipped_blank = 0
		if user == USER_NARRATIVE:
			message = {"content": content}
		else:
			message = {"user": user, "content": content}

	if message is not None:
		logger.debug(message)
		yield message


def test_split_message_line():
	line = "Ally:	Hello\n"
	user, content = split_message_line(line)
	assert user == "Ally"
	assert content == "Hello\n"


def test_lines_to_messages():
	lines = """Ally:	Hello
	World
Sam:	How are you?
"""
	messages = list(lines_to_messages(lines.splitlines()))
	assert len(messages) == 2
	assert messages[0]["user"] == "Ally"
	assert messages[0]["content"] == "Hello\nWorld\n"
	assert messages[1]["user"] == "Sam"
	assert messages[1]["content"] == "How are you?\n"


def message_to_text(message):
	""" Convert a chat message to text. """
	user = message.get("user")
	content = message["content"]
	if user:
		lines = content.splitlines() or [""]
		lines2 = []
		lines2.append(f"{user}:\t{lines[0]}\n")
		for line in lines[1:]:
			lines2.append(f"\t{line}\n")
		text = "".join(lines2)
	else:
		text = content
	return text.rstrip()+"\n"


def preprocess(content):
	""" Preprocess chat message content, for markdown-katex """

	# replace $foo$ with $`foo`$
	# replace $$\n...\n$$ with ```math\n...\n```

	out = []

	in_math = False
	for line in content.splitlines():
		if line == "$$" and not in_math:
			out.append("```math")
			in_math = True
		elif line == "$$" and in_math:
			out.append("```")
			in_math = False
		else:
			line = re.sub(r'\$(.*?)\$', r'$`\1`$', line)
			out.append(line)

	content = "\n".join(out)+"\n"
	logger.warning("preprocess content: %r", content)
	return content


def message_to_html(message):
	""" Convert a chat message to HTML. """
	logger.debug("converting message to html: %r", message["content"])
	content = preprocess(message["content"])
	html_content = markdown.markdown(content, extensions=MARKDOWN_EXTENSIONS, extension_configs=MARKDOWN_EXTENSION_CONFIGS)
	logger.debug("html_content: %r", html_content)
	if html_content == "":
		html_content = "&nbsp;"
	user = message.get("user")
	if user:
		user_ee = html.escape(user)
		return f"""<div class="message" user="{user_ee}"><div class="label">{user_ee}:</div><div class="content">{html_content}</div></div>"""
	return f"""<div class="narrative"><div class="content">{html_content}</div></div>"""


#@argh.arg('--doctype', nargs='?')
#@argh.arg('--stylesheets', nargs='*', type=str, default=["/room.css"])
#@argh.arg('--scripts', nargs='*', type=str, default=["https://ucm.dev/js/util.js", "/room.js"])
#def chat_to_html(doctype="html", stylesheets=None, scripts=None):
def chat_to_html():
	""" Convert an Allemande chat file to HTML. """
#	if doctype:
#		print(f"""<!DOCTYPE {doctype}>""")
#	for src in stylesheets:
#		print(f"""<link rel="stylesheet" href="{html.escape(src)}">""")
#	for src in scripts:
#		print(f"""<script src="{html.escape(src)}"></script>""")
	for message in lines_to_messages(sys.stdin.buffer):
		print(message_to_html(message))


if __name__ == '__main__':
	argh.dispatch_command(chat_to_html)
