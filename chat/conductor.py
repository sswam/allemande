#!/usr/bin/env python3-allemande

""" conductor.py: decide which agent/s should respond to a message """

import logging
import re


logger = logging.getLogger(__name__)


# disabled "everyone" for now; keep it simple
# EVERYONE_WORDS = ["everyone", "anyone", "all", "y'all"]


def find_name_in_content(content, name, ignore_case=True):
	""" try to find a name in message content """
	start_comma_word = r'^\s*' + re.escape(name) + r'\b\s*,'
	comma_word_end = r',\s*' + re.escape(name) + r'\b\s*[\.!?]?\s*$'
	word_start = r'^\s*' + re.escape(name) + r'\b'
	word_end = r'\b' + re.escape(name) + r'\b\s*[\.!?]?\s*$'
	whole_word = r'\b' + re.escape(name) + r'\b'

	flags = re.IGNORECASE if ignore_case else 0

	for i, regexp in enumerate([start_comma_word, comma_word_end, word_start, word_end, whole_word]):
		if match := re.search(regexp, content, flags):
			return (i, match.start(), name)

	return (100, len(content), None)


def who_is_named(content, user, agents, include_self=True):
	""" check who is named first in the message """
#	matches = [find_name_in_content(content, agent) for agent in agents + EVERYONE_WORDS]
	logger.warning("content %r", content)
	matches = [find_name_in_content(content, agent) for agent in agents]
	if not include_self and user:
		matches = [m for m in matches if m[2] and m[2].lower() != user.lower()]
	if not matches:
		return []
	logger.warning("who_is_named, matches: %r", matches)
	_type, _pos, agent = min(matches)
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
