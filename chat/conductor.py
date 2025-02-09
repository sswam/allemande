#!/usr/bin/env python3-allemande

""" conductor.py: decide which agent/s should respond to a message """

import logging
import re
import random
from typing import Any


logger = logging.getLogger(__name__)

EVERYONE_WORDS = [
    # General plural addresses
    "everyone",
    "everybody",
    "y'all",
    "you all",
    "all of you",
    #    "folks", "people",
    #    "gang", "crew", "team",
]

ANYONE_WORDS = [
    "anyone",
    "anybody",
    "someone",
    "somebody",
    "one of you",
    "one of y'all",
    "who's next",
    "who wants to",
]


# TODO exclude based on an attribute or settings
EXCLUDE_PARTICIPANTS = set(["System", "Sia", "Nova", "Pixi", "Brie", "Chaz", "Atla", "Pliny", "Morf"])

USE_PLURALS = True


def find_name_in_content(content: str, name: str, ignore_case: bool = True) -> tuple[int, int, str | None]:
    """try to find a name in message content"""
    logger.debug("find_name_in_content: %r %r %r", content, name, ignore_case)
    start_comma_word = r"(?m)^\s*" + re.escape(name) + r"\b\s*,"  # matches at the start of any line
    comma_word_end = r",\s*" + re.escape(name) + r"\b\s*\W*]?\s*$"
    word_start = r"^\s*" + re.escape(name) + r"\b"
    word_end = r"(\s|\b)" + re.escape(name) + r"\b\s*[\.!?]?\s*$"
    whole_word = r"(\s|\b)" + re.escape(name) + r"\b"

    flags = re.IGNORECASE if ignore_case else 0

    for i, regexp in enumerate([start_comma_word, comma_word_end, word_start, word_end, whole_word]):
        if match := re.search(regexp, content, flags):
            logger.debug("find_name_in_content match: %r", (i, match.start(), name))
            return (i, match.start(), name)

    logger.debug("find_name_in_content no match: %r", (100, len(content), None))
    return (100, len(content), None)


def uniqo(l: list[Any]) -> list[Any]:
    """remove duplicates from a list while preserving order"""
    return list(dict.fromkeys(l))


def who_is_named(
    content: str,
    user: str | None,
    agents: list[str],
    include_self: bool = True,
    chat_participants: list[str] | None = None,
    everyone_words: list[str] | None = None,
    anyone_words: list[str] | None = None,
    get_all: bool = False,
) -> list[str]:
    """check who is named first in the message"""
    if chat_participants is None:
        chat_participants = []
    if everyone_words is None:
        everyone_words = []
    if anyone_words is None:
        anyone_words = []

    logger.warning(
        "who_is_named: %r %r %r %r %r %r %r", content, user, agents, include_self, chat_participants, everyone_words, anyone_words
    )

    # Calculate everyone_except_user before using in function
    if user:
        user_clean = user.lstrip("@")
        everyone_except_user = [a for a in chat_participants if a != user_clean]
    else:
        everyone_except_user = chat_participants

    agents_and_plurals = agents
    if USE_PLURALS:
        agents_and_plurals = agents + everyone_words + anyone_words
    matches = [find_name_in_content(content, agent) for agent in agents_and_plurals]
    if not include_self and user:
        matches = [m for m in matches if m[2] and m[2].lower() != user.lower()]
    if not matches:
        return []

    logger.warning("matches: %r", matches)

    # Sort matches by position and type, preserving only lowest indices
    # sorted_matches = sorted(matches, key=lambda x: (x[0], x[1]))
    if not get_all:
        matches = [min(matches)]
    result = []

    logger.warning("matches 2: %r", matches)

    result: list[str] = []
    for _type, _pos, agent in matches:
        if agent is None:
            continue
        if agent in everyone_words:
            random.shuffle(everyone_except_user)
            result.extend(everyone_except_user)
        elif agent in anyone_words and everyone_except_user:
            result.append(random.choice(everyone_except_user))
        else:
            result.append(agent)

    result = [x.lstrip("@") for x in result]
    result = uniqo(result)

    logger.warning("who_is_named result: %r", result)

    return result


def who_spoke_last(
    history: list[dict[str, Any]],
    user: str | None,
    agents: dict[str, dict[str, Any]],
    include_self: bool = False,
    include_humans: bool = True,
    include_tools: bool = False,
) -> list[str]:
    """check who else spoke in recent history"""
    user_lc = user.lower() if user is not None else None
    for i in range(len(history) - 1, -1, -1):
        user2 = history[i].get("user")
        if user2 is None:
            continue
        user2_lc = user2.lower() if user2 is not None else None
        if (
            user2_lc in agents
            and (include_self or user2_lc != user_lc)
            and (include_tools or not agent_is_tool(agents[user2_lc]))
            and (include_humans or not agent_is_human(agents[user2_lc]))
        ):
            return [user2]
    return []


def participants(history: list[dict[str, str]]) -> list[str]:
    """get all participants in the history"""
    agents = list(set(x["user"] for x in history if x.get("user")) - EXCLUDE_PARTICIPANTS)
    return agents


def agent_is_tool(agent: dict[str, Any]) -> bool:
    """check if an agent is a tool"""
    return agent.get("type") == "tool" or agent.get("service") == "image_a1111"


def agent_is_human(agent: dict[str, Any]) -> bool:
    """check if an agent is a human"""
    return agent.get("type") == "person"


def agent_is_ai(agent: dict[str, Any]) -> bool:
    """check if an agent is an AI"""
    return not agent_is_tool(agent) and not agent_is_human(agent)


def who_should_respond(
    message: dict[str, Any]|None,
    agents: dict[str, dict[str, Any]] | None = None,
    history: list[dict[str, Any]] | None = None,
    default: list[str] | None = None,
    include_self: bool = True,
    include_humans: bool = True,
) -> list[str]:
    """who should respond to a message"""
    if not history:
        history = []
    if not agents:
        agents = {}

    agents = agents.copy()

    all_participants: list[str] = participants(history)

    logger.warning("all_participants: %r", all_participants)

    # Add agents for humans in the history
    for agent in all_participants:
        agent_lc = agent.lower()
        if agent_lc not in agents:
            agents[agent_lc] = {
                "name": agent,
                "type": "person",
            }

    agent_names = list(agents.keys())
    agents_lc = list(map(str.lower, agent_names))
    #    agents_lc_to_agents = dict(zip(agents_lc, agents))
    agent_case_map = {k.lower(): agents[k]["name"] for k in agents}

    user = message.get("user") if message else None
    user_lc = user.lower() if user else None

    logger.warning("user, user_lc: %r %r", user, user_lc)

    if user_lc in agents_lc:
        user_agent = agents[user_lc]
        logger.warning('user_agent["type"]: %r', user_agent["type"])
        if user_agent["type"] == "tool":
            invoked = who_spoke_last(history[:-1], user, agents, include_self=include_self, include_humans=include_humans)
            return [agent_case_map[i.lower()] for i in invoked]

    is_person = user_lc in agents_lc and agents[user_lc]["type"] == "person"

    if not is_person:
        include_self = False

    # Filter chat participants based on include_humans setting
    chat_participants_names_lc = [
        agent
        for agent in all_participants
        if agents[agent.lower()]["type"] != "tool"
        and agents[agent.lower()].get("service") != "image_a1111"
        and (include_humans or agents[agent.lower()]["type"] != "person")
    ]

    logger.warning("chat_participants_names_lc: %r", chat_participants_names_lc)

    content = message["content"] if message else ""

    # Filter out human users if requested from agent_names
    if not include_humans:
        agent_names = [name for name in agent_names if agents[name]["type"] != "person"]

    agents_names_with_at = [f"@{name}" for name in agent_names]

    everyone = EVERYONE_WORDS if USE_PLURALS else []
    anyone = ANYONE_WORDS if USE_PLURALS else []
    everyone_with_at = [f"@{agent}" for agent in everyone]
    anyone_with_at = [f"@{agent}" for agent in anyone]

    # For @mode, all mentioned agents should reply
    invoked = who_is_named(
        content,
        f"@{user}",
        agents_names_with_at,
        include_self=include_self,
        chat_participants=chat_participants_names_lc,
        everyone_words=everyone_with_at,
        anyone_words=anyone_with_at,
        get_all=True,
    )

    logger.warning("who_is_named @: %r", invoked)
    if not invoked:
        invoked = who_is_named(
            content,
            user,
            agent_names,
            include_self=include_self,
            chat_participants=chat_participants_names_lc,
            everyone_words=everyone,
            anyone_words=anyone,
        )
        logger.warning("who_is_named 2: %r", invoked)
    if not invoked:
        invoked = who_spoke_last(history[:-1], user, agents, include_self=include_self, include_humans=include_humans)
        logger.warning("who_spoke_last: %r", invoked)

    # If still no one to respond, default to last AI speaker or random AI
    if not invoked:
        ai_participants = [agent for agent in all_participants if agent_is_ai(agents[agent.lower()])]
        last_ai = None
        if ai_participants:
            invoked = who_spoke_last(history[:-1], user, ai_participants, include_self=True, include_humans=False)
            logger.warning("who_spoke_last ai: %r", invoked)
        if not invoked and ai_participants:
            invoked = [random.choice(ai_participants)]
            logger.warning("random ai: %r", invoked)
        if not invoked and default:
            invoked = [random.choice(default)]
            logger.warning("default: %r", invoked)

    # Filter out special words and only use actual agent names
    return [agent_case_map[agent.lower()] for agent in invoked if agent.lower() in agent_case_map]
