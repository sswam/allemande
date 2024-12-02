#!/usr/bin/env python3-allemande

""" conductor.py: decide which agent/s should respond to a message and invoke them """

import sys
import argparse
import logging
from pathlib import Path
import re
import random

from watchfiles import Change
import regex

import ucm
import atail
import chat


logger = logging.getLogger(__name__)


# disabled "everyone" for now; keep it simple
# EVERYONE_WORDS = ["everyone", "anyone", "all", "y'all"]


def find_name_in_content(content, name, ignore_case=True):
	""" try to find a name in message content """
	whole_word = r'\b' + re.escape(name) + r'\b'
	flags = re.IGNORECASE if ignore_case else 0
	match = re.search(whole_word, content, flags)
	if match:
		return (match.start(), name)
	return (len(content), None)


def who_is_named(content, user, agents, include_self=True):
	""" check who is named first in the message """
#	matches = [find_name_in_content(content, agent) for agent in agents + EVERYONE_WORDS]
	logger.warning("content %r", content)
	matches = [find_name_in_content(content, agent) for agent in agents]
	if not include_self and user:
		matches = [m for m in matches if m[1] and m[1].lower() != user.lower()]
	if not matches:
		return []
	logger.warning("who_is_named, matches: %r", matches)
	_pos, agent = min(matches)
	if agent is None:
		invoked = []
#	elif agent in EVERYONE_WORDS and include_self:
#		invoked = agents
#	elif agent in EVERYONE_WORDS:
#		invoked = [a for a in agents if a != user]
	else:
		invoked = [agent]
	return invoked


def who_spoke_last(history, user, agents, include_self=False):
	""" check who else spoke in recent history """
	user_lc = user.lower() if user is not None else None
	for i in range(len(history)-1, -1, -1):
		user2 = history[i].get("user")
		if user2 is None:
			continue
		user2_lc = user2.lower() if user2 is not None else None
		if user2_lc in agents and (include_self or user2_lc != user_lc) and agents[user2_lc]["type"] != "tool":
			return [user2]
	return []


def participants(history):
	agents = list(set(x.get("user") for x in history if x.get("user")))
	return agents


def who_should_respond(message, agents=None, history=None, default=None, include_self=True):
	""" who should respond to a message """
	if not history:
		history = []
	if not agents:
		agents = []

	agents = agents.copy()

	all_people = participants(history)
	for person in all_people:
		person_lc = person.lower()
		if person_lc not in agents:
			agents[person_lc] = {
				"name": person,
				"type": "person",
			}

	agent_names = list(agents.keys())

	agents_lc = list(map(str.lower, agent_names))

	agents_lc_to_agents = dict(zip(agents_lc, agents))

	user = message.get("user")
	if user:
		user_lc = user.lower()
	else:
		user_lc = None

	logger.warning("user, user_lc: %r %r", user, user_lc)

	if user_lc in agents_lc:
		user_agent = agents[user_lc]
		logger.warning('user_agent["type"]: %r', user_agent["type"])
		if user_agent["type"] == "tool":
			invoked = who_spoke_last(history[:-1], user, agents, include_self=include_self)
			return invoked

	is_person = user_lc in agents_lc and agents[user_lc]["type"] == "person"

	if not is_person:
		include_self = False

	content = message["content"]

	agents_with_at = [f"@{agent}" for agent in agent_names]

	invoked = who_is_named(content, f"@{user}", agents_with_at, include_self=include_self)
	logger.warning("who_is_named @: %r", invoked)
	if not invoked:
		invoked = who_is_named(content, user, agent_names, include_self=include_self)
		logger.warning("who_is_named 2: %r", invoked)
	if not invoked:
		invoked = who_spoke_last(history[:-1], user, agents, include_self=include_self)
		logger.warning("who_spoke_last 2: %r", invoked)
	if not invoked and default and user_lc != default.lower() and agents[user_lc]["type"] == "person":
		invoked = [default]
		logger.warning("default %r", invoked)

	invoked = [agents_lc_to_agents.get(agent_lc, agent_lc) for agent_lc in invoked]

	return invoked


class ConductorOptions: # pylint: disable=too-few-public-methods
	""" the options for the Conductor class """
	exts = ()


class Conductor:
	""" decide which agent/s should respond to a message and invoke them """

	def __init__(self, opts, watch_log):
		""" Initialize the Conductor object """
		self.opts = opts
		self.watch_log = watch_log
		self.tail = atail.AsyncTail(filename=self.watch_log, follow=True, rewind=True).run()

	async def run(self):
		""" watch bb chat files, and invoke agents to reply to them where appropriate """
		# TODO factor this with bb2html
		logger.debug("opts: %s", self.opts)
		async for line in self.tail:
			logger.debug("line from tail: %s", line)
			bb_file, change_type, old_size, new_size = line.rstrip("\n").split("\t")
			change_type = Change(int(change_type))
			old_size = int(old_size) if old_size != "" else None
			new_size = int(new_size) if new_size != "" else None
			if not bb_file.endswith(self.opts.exts):
				continue
			html_file = str(Path(bb_file).with_suffix(".html"))
			if change_type == Change.deleted:
				Path(html_file).unlink(missing_ok=True)
				continue
			async for row in self.file_changed(bb_file, html_file, old_size, new_size):
				yield row

	async def file_changed(self, bb_file, html_file, old_size, new_size):
		""" check which agent to invoke, if any, and invoke it """
		pass

#		# assume the file was appended to ...
#		html_file_mode = "a"
#
#		# ... unless the file has shrunk
#		if old_size and new_size < old_size:
#			logger.warning("bb file was truncated: %s from %s to %s", bb_file, old_size, new_size)
#			html_file_mode = "w"
#
#		with open(bb_file, "r", encoding="utf-8") as bb:
#			with open(html_file, html_file_mode, encoding="utf-8") as html:
#				html_file_size = html.tell()
#				if old_size and html_file_size:
#					bb.seek(old_size)
#				for message in chat.lines_to_messages(bb):
#					print(chat.message_to_html(message), file=html)
#				row = [html_file]
#				yield row

async def conductor_main(opts, watch_log, out=sys.stdout):
	""" Main function """
	conductor = Conductor(opts=opts, watch_log=watch_log)
	async for row in conductor.run():
		print(*row, sep="\t", file=out)


def get_opts():
	""" Get the command line options """
	parser = argparse.ArgumentParser(description="conductor: decide which agent/s should respond to the chat and invoke them", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
	parser.add_argument('-w', '--watch-log', default="/dev/stdin", help="the file where changes are logged")
	parser.add_argument('-x', '--extension', nargs="*", default=("bb",), help="the file extensions to process")
	ucm.add_logging_options(parser)
	opts = parser.parse_args()
	return opts


def main():
	""" Main function """
	opts = get_opts()
	ucm.setup_logging(opts)
	exts = tuple(f".{ext}" for ext in opts.extension or ())
	opts.exts = exts
	ucm.run_async(conductor_main(opts=opts, watch_log=opts.watch_log))


if __name__ == '__main__':
	main()


# The term "agent" includes humans, AI bots, and non-AI software agents.

# We could detect vocative phrases (e.g. "Hi Name") and respond to them.

# To keep it simple, just detect if any agent is named, and the first agent
# named is the one invoked.

# TODO perhaps if the agent's name is a single letter or a common noun, we
# should not ignore case e.g. if an agent was called "C" or "And" or "Python".

# TODO distinguish human agents, AI agents, and non-AI software agents.
# "anyone" and "everyone" would refer to AI agents.
# The conductor could never force a human to respond, but it might notify the
# user more loudly than normal.

# anyone should be a random choice among AI-agents or humans maybe:
# from random import choice

# This is just a rough prototype. Going forward we could use a more
# sophisticated NLP library like spaCy or a model, if necessary.

# TODO should the conductor actually add the agent's invitation to the file?  like Foo:
# Or how will it fit in to the scheme of things?

# bb2html reads the watch.log
# I think that other independent processes can also read the watch.log, that should be okay.
# We could assume that each agent runs a core process, using port directories to communicate with clients.
# Perhaps the conductor process can tie it all together, that would make sense.
# In that case, this library might be called who instead of conductor.



regex_name = r"^[\p{L}\p{M}']+([\p{Zs}\-][\p{L}\p{M}']+)*$"

# Matches names containing letters, diacritics, apostrophes, with optional spaces/hyphens between parts. Requires minimum 1 character. Disallows consecutive spaces/hyphens or spaces/hyphens at start/end.

# \p{L} - letters
# \p{M} - marks/diacritics
# \p{Zs} - spaces
# ' - apostrophes
# \- - hyphens


# TODO lib
def uniqo(l):
	# unique in order
	return list(dict.fromkeys(l))


# obsolescent get_roles_from_history function --------------------------------------

def get_roles_from_history(history, user, bot):
	""" Get the latest user and bot names from history """

	recent = reversed(history[-20:])
	print("recent: ", recent)
	roles = map(lambda line: line.split(":")[0], recent)
	print("roles: ", roles)
	roles = uniqo(roles)
	print("roles: ", roles)
	roles = list(filter(lambda role: role and regex.match(regex_name, role), roles))
	print("roles: ", roles)
	if roles:
		user = roles[0]
#	What did this do?!
#	if len(roles) > 1 and random.random() < 0.5 and "Ally" in roles and user != "Ally":
#		return user, "Ally"
	if len(roles) > 1:
		# return a random out of the remaining roles
		bot = random.choice(roles[1:])
	print("user, bot:", user, bot)

	return user, bot

