#!/usr/bin/env python3

""" chat.py: Allemande chat file format library """

import sys
import itertools
import html

import argh
import markdown


USER_NARRATIVE = object()
USER_CONTINUED = object()


def split_message_line(line):
	""" Split a message line into user and content. """

	if "\t" in line:
		label, content = line.split("\t", 1)
	else:
		label = None
		content = line

	if label is None:
		user = USER_NARRATIVE
	elif label == "":
		user = USER_CONTINUED
	elif label.endswith(":"):
		user = label[:-1]
	else:
		raise ValueError("Invalid label missing colon, in line: %s" % line)

	return user, content


def lines_to_messages(lines):
	""" A generator to convert an iterable of lines to chat messages. """

	message = None

	# add a sentinel blank line
	lines = itertools.chain(lines, [""])

	while True:
		line = next(lines, None)
		if line is None:
			break

		user, content = split_message_line(line)

		# accumulate continued lines
		if message and user == USER_CONTINUED:
			message["content"] += content
			continue

		if not message and user == USER_CONTINUED:
			raise ValueError("Continued line with no previous incomplete message: %s" % line)

		# yield the previous message
		if message:
			yield message
			message = None

		# skip blank lines
		if user == USER_NARRATIVE and content.rstrip("\r\n") == "":
			continue

		# start a new message
		if user == USER_NARRATIVE:
			message = {"content": content}
		else:
			message = {"user": user, "content": content}


def message_to_html(message):
	""" Convert a chat message to HTML. """
	html_content = markdown.markdown(message["content"])
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
	for message in lines_to_messages(sys.stdin):
		print(message_to_html(message))


if __name__ == '__main__':
	argh.dispatch_command(chat_to_html)
