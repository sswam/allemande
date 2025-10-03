#!/usr/bin/env python3-allemande

""" who_is_named.py: find who is named in a message """

import re
import random
import logging
from typing import Any, Iterable

from util import uniqo
from agents import Agents
import chat
from conductor_settings import *
from text.names import extract_partial_names, NAME_PATTERN

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

__version__ = "0.2.1"


def agent_is_tool(agent: dict[str, Any]) -> bool:
    """check if an agent is a tool"""
    agent_type = agent.get("type")
    return agent.get("link") == "tool" or (agent_type and agent_type.startswith("image_"))


def filter_access(invoked: Iterable[str], room: chat.Room | None, access_check_cache: dict[str, int], agent_name_map: dict[str, str], must_exist: bool = True) -> list[str]:
    """filter out agents that don't have access"""
    if not room:
        return list(invoked)
    result = []
    for agent in invoked:
        agent = re.sub(r"^@", "", agent)
        agent_lc = agent.lower()
        if must_exist and agent_lc not in agent_name_map:
            continue
        agent = agent_name_map.get(agent_lc, agent)
        if access_check_cache.get(agent_lc) is None:
            access_check_cache[agent_lc] = room.check_access(agent_lc).value
        if access_check_cache[agent_lc] & chat.Access.READ_WRITE.value:
            result.append(agent)
    return result


def find_name_in_content(content: str, name: str, ignore_case: bool = True, is_tool: bool = False) -> tuple[int, int, int, str | None] | None:  # pylint: disable=too-many-locals
    """
    Try to find a name in message content, prioritizing later sentences
    Returns tuple of (match_type, sentence_num_from_end, position, name)
    match_type: 0-4 for different match types, 100 for no match
    sentence_num_from_end: 0 for last sentence, counting up for earlier ones

    The matching logic:
    - Lower match_type numbers have higher priority (0-4)
    - Within the same match_type, later sentences (lower sentence_num) have priority
    - Within the same sentence, earlier positions have priority

    Note: The sentence splitting is very simple and can be improved.
    """
    # logger.debug("find_name_in_content: %r %r %r", content, name, ignore_case)

    # Define match patterns
    start_comma_word = r"^\s*`*" + re.escape(name) + r"\b\s*(,|$)"  # at start with comma, or whole line, also allow backticks for code quoting

    patterns = [start_comma_word]

    if not is_tool:
        comma_word_end = r",\s*" + re.escape(name) + r"\b\s*\W*$"  # at end with comma
        word_start = r"^\s*" + re.escape(name) + r"\b"  # at start
        word_end = r"(\W|^)" + re.escape(name) + r"\b\s*[\.!?]?\s*$"  # at end
        whole_word = r"(\W|^)" + re.escape(name) + r"\b"  # anywhere
        patterns += [comma_word_end, word_start, word_end, whole_word]

    flags = re.IGNORECASE if ignore_case else 0

    # Split into sentences
    best_match = (100, -1, len(content), 0, "")  # (match_type, sentence_num, position, length, name)

    length = len(name)

    sentences = re.split(r'[.!?]+\s+|\n+', content)
    for sent_num, sentence in enumerate(reversed(sentences)):  # reverse to prioritize later sentences
        for match_type, pattern in enumerate(patterns):
            if match := re.search(pattern, sentence, flags):
                # Calculate absolute position in original content
                abs_pos = content.find(sentence) + match.start()
                current_match = (match_type, sent_num, abs_pos, -length, name)
                best_match = min(best_match, current_match)

    if best_match[4]:
        return (best_match[0], best_match[1], best_match[2], best_match[4])
    return None


def who_is_named(  # pylint: disable=too-many-arguments, too-many-positional-arguments, too-many-locals, too-many-branches, too-many-statements
    content: str,
    user: str,
    agent_names: list[str],
    include_self: bool = True,
    chat_participants: list[str] | None = None,
    chat_participants_all: list[str] | None = None,
    everyone_words: list[str] | None = None,
    anyone_words: list[str] | None = None,
    self_words: list[str] | None = None,
    get_all: bool = False,
    room: chat.Room | None = None,
    access_check_cache: dict[str, int] | None = None,
    agents: Agents | None = None,
    ignore_case: bool = True,
    uniq: bool = True,
    agent_name_map: dict[str, str] | None = None,
) -> list[str]:
    """check who is named first in the message"""
    if chat_participants is None:
        chat_participants = []
    if chat_participants_all is None:
        chat_participants_all = []
    if everyone_words is None:
        everyone_words = []
    if anyone_words is None:
        anyone_words = []
    if self_words is None:
        self_words = []
    if access_check_cache is None:
        access_check_cache = {}
    if agent_name_map is None:
        agent_name_map = {}

    logger.debug(
        "who_is_named: %r %r %r %r %r %r %r %r %r %r", content, user, agent_names, include_self, chat_participants, chat_participants_all, everyone_words, anyone_words, self_words, get_all
    )

    # Calculate everyone_except_user
    everyone_except_user = [a for a in chat_participants if a != user]
    everyone_except_user_all = [a for a in chat_participants_all if a != user]

    # Extract candidate names from content using names library
    candidate_names = set()
    for match in NAME_PATTERN.finditer(content, overlapped=True):
        name = match.group().strip()
        # Get all partial names (subsequences)
        candidate_names.update(extract_partial_names(name))

    logger.debug("candidate_names: %r", candidate_names)

    # Build set of all possible agent names to match against
    agents_and_plurals = agent_names
    if USE_PLURALS:
        agents_and_plurals = agent_names + everyone_words + anyone_words + self_words

    # Create lowercase lookup for case-insensitive matching
    agent_lookup = {}
    for agent in agents_and_plurals:
        key = agent.lower() if ignore_case else agent
        agent_lookup[key] = agent

    # Match candidates against agents
    matches = []
    for candidate in candidate_names:
        candidate_key = candidate.lower() if ignore_case else candidate
        if candidate_key in agent_lookup:
            agent = agent_lookup[candidate_key]
            is_tool = agents is not None and agent in agents.agents and agent_is_tool(agents.get(agent))
            best_match = find_name_in_content(content, agent, is_tool=is_tool, ignore_case=ignore_case)
            if best_match:
                matches.append(best_match)

    if not include_self and user:
        matches = [m for m in matches if m[3] and m[3] != user]
    if not matches:
        return []

    logger.debug("matches: %r", matches)

    # Sort matches by position and type, preserving only lowest indices
    # sorted_matches = sorted(matches, key=lambda x: (x[0], x[1]))
    if not get_all:
        matches = [min(matches)]

    logger.debug("matches 2: %r", matches)

    logger.debug("%r", everyone_except_user)
    logger.debug("%r", everyone_except_user_all)

    result: list[str] = []
    for _type, _sentence, _pos, agent in matches:
        if agent is None:
            continue
        if agent in everyone_words:
            random.shuffle(everyone_except_user)
            if EVERYONE_MAX is not None:
                result.extend(everyone_except_user[:EVERYONE_MAX])
            else:
                result.extend(everyone_except_user)
        elif agent in anyone_words and everyone_except_user:
            result.append(random.choice(everyone_except_user))
        elif agent in anyone_words and everyone_except_user_all:
            result.append(random.choice(everyone_except_user_all))
        elif agent in self_words and user:
            result.append(user)
        else:
            logger.info("checking access for %r", agent)
            if filter_access([agent], room, access_check_cache, agent_name_map):
                logger.info("access granted for %r", agent)
                result.append(agent)
            else:
                logger.info("access denied for %r", agent)

    result = [x.lstrip("@") for x in result]
    if uniq:
        result = uniqo(result)

    logger.debug("who_is_named result: %r", result)

    return result
