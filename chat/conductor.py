#!/usr/bin/env python3-allemande

""" conductor.py: decide which agent/s should respond to a message """

import logging
import re
import random
from typing import Any

import chat

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
    "who's up next",
    "who's ready",
    "who's going to",
    "who is next",
    "who is ready",
    "who is going",
    "who wants to",
    "who else",
]

# TODO configureable by room

# TODO exclude based on an attribute or settings
EXCLUDE_PARTICIPANTS = set(["System", "Sia", "Nova", "Pixi", "Brie", "Chaz", "Atla", "Pliny", "Morf", "Palc", "Dogu", "Gid", "Lary", "Matz", "Luah", "Jyan", "Jahl", "Faby", "Qell", "Bilda"])
# EXCLUDE_PARTICIPANTS = set(["System", "Palc", "Dogu", "Gid", "Lary", "Matz", "Luah", "Jyan", "Jahl", "Faby", "Qell", "Bilda"])
EXCLUDE_PARTICIPANTS_SYSTEM = set(["System"])

EVERYONE_MAX = 5
AI_EVERYONE_MAX = 2

USE_PLURALS = True


def find_name_in_content(content: str, name: str, ignore_case: bool = True) -> tuple[int, int, int, str | None]:
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
    logger.debug("find_name_in_content: %r %r %r", content, name, ignore_case)

    # Define match patterns
    start_comma_word = r"^\s*" + re.escape(name) + r"\b\s*,"  # at start with comma
    comma_word_end = r",\s*" + re.escape(name) + r"\b\s*\W*$"  # at end with comma
    word_start = r"^\s*" + re.escape(name) + r"\b"  # at start
    word_end = r"(\s|\b)" + re.escape(name) + r"\b\s*[\.!?]?\s*$"  # at end
    whole_word = r"(\s|\b)" + re.escape(name) + r"\b"  # anywhere

    patterns = [start_comma_word, comma_word_end, word_start, word_end, whole_word]
    flags = re.IGNORECASE if ignore_case else 0

    # Split into sentences
    best_match = (100, -1, len(content), None)  # (match_type, sentence_num, position, name)

    sentences = re.split(r'[.!?\n]+', content)
    for sent_num, sentence in enumerate(reversed(sentences)):  # reverse to prioritize later sentences
        for match_type, pattern in enumerate(patterns):
            if match := re.search(pattern, sentence, flags):
                # Calculate absolute position in original content
                abs_pos = content.find(sentence) + match.start()
                current_match = (match_type, sent_num, abs_pos, name)

                # Update if this is a better match
                if current_match < best_match:
                    best_match = current_match

    return best_match


def uniqo(l: list[Any]) -> list[Any]:
    """remove duplicates from a list while preserving order"""
    return list(dict.fromkeys(l))


def who_is_named(
    content: str,
    user: str | None,
    agent_names: list[str],
    include_self: bool = True,
    chat_participants: list[str] | None = None,
    chat_participants_all: list[str] | None = None,
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

    logger.debug(
        "who_is_named: %r %r %r %r %r %r %r", content, user, agent_names, include_self, chat_participants, everyone_words, anyone_words
    )

    # Calculate everyone_except_user before using in function
    if user:
        user_clean = user.lstrip("@")
        everyone_except_user = [a for a in chat_participants if a != user_clean]
        everyone_except_user_all = [a for a in chat_participants_all if a != user_clean]
    else:
        everyone_except_user = chat_participants
        everyone_except_user_all = chat_participants_all

    agents_and_plurals = agent_names
    if USE_PLURALS:
        agents_and_plurals = agent_names + everyone_words + anyone_words
    matches = [find_name_in_content(content, agent) for agent in agents_and_plurals]
    if not include_self and user:
        matches = [m for m in matches if m[3] and m[3].lower() != user.lower()]
    if not matches:
        return []

#    logger.debug("matches: %r", matches)

    # Sort matches by position and type, preserving only lowest indices
    # sorted_matches = sorted(matches, key=lambda x: (x[0], x[1]))
    if not get_all:
        matches = [min(matches)]

#    logger.debug("matches 2: %r", matches)

    logger.debug(f"{everyone_except_user=}")
    logger.debug(f"{everyone_except_user_all=}")

    result: list[str] = []
    for _type, _sentence, _pos, agent in matches:
        if agent is None:
            continue
        if agent in everyone_words:
            random.shuffle(everyone_except_user)
            result.extend(everyone_except_user[:EVERYONE_MAX])
        elif agent in anyone_words and everyone_except_user:
            result.append(random.choice(everyone_except_user))
        elif agent in anyone_words and everyone_except_user_all:
            result.append(random.choice(everyone_except_user_all))
        else:
            result.append(agent)

    result = [x.lstrip("@") for x in result]
    result = uniqo(result)

    logger.debug("who_is_named result: %r", result)

    return result


def who_spoke_last(
    history: list[dict[str, Any]],
    user: str | None,
    agents_dict: dict[str, dict[str, Any]],
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
        if user2 in EXCLUDE_PARTICIPANTS_SYSTEM:
            continue
        user2_lc = user2.lower() if user2 is not None else None
        if (
            user2_lc in agents_dict
            and (include_self or user2_lc != user_lc)
            and (include_tools or not agent_is_tool(agents_dict[user2_lc]))
            and (include_humans or not agent_is_human(agents_dict[user2_lc]))
        ):
            return [user2]
    return []


def participants(history: list[dict[str, str]], use_all=False) -> list[str]:
    """get all participants in the history"""
    agents_set = set(x["user"] for x in history if x.get("user"))
    agents_set -= EXCLUDE_PARTICIPANTS_SYSTEM
    if not use_all:
        agents_set -= EXCLUDE_PARTICIPANTS
    return list(agents_set)


def agent_is_tool(agent: dict[str, Any]) -> bool:
    """check if an agent is a tool"""
    return agent.get("link") == "tool" or agent.get("type") == "image_a1111"


def agent_is_human(agent: dict[str, Any]) -> bool:
    """check if an agent is a human"""
    return agent.get("type") == "human"


def agent_is_ai(agent: dict[str, Any]) -> bool:
    """check if an agent is an AI"""
    return not agent_is_tool(agent) and not agent_is_human(agent)


def is_image_message(agents_dict: dict[str, dict[str, Any]], message: dict[str, str]) -> bool:
    agent = agents_dict.get(message.get("user"))
    if not agent:
        return False
    service = agent.get("type")
    return service and service.startswith("image_")


def who_should_respond(
    message: dict[str, Any] | None,
    agents_dict: dict[str, dict[str, Any]] | None = None,
    history: list[dict[str, Any]] | None = None,
    default: list[str] | None = None,
    include_self: bool = True,
    include_humans_for_ai_message: bool = True,
    include_humans_for_human_message: bool = True,
    config: dict[str, Any] | None = None,
    mission: str | None = None,
) -> list[str]:
    """who should respond to a message"""
    logger.debug("who_should_respond: %r %r", message, history)
    if not history:
        history = []
    if not agents_dict:
        agents_dict = {}

    if config.get("skip_image_replies"):
        history = [m for m in history if not is_image_message(agents_dict, m)]
        if history:
            message = history[-1]
        else:
            message = None

    history = chat.history_remove_thinking_sections(history, None)

    direct_reply_chance = config.get("direct_reply_chance", 1.0)

    agents_dict = agents_dict.copy()

    # mentioned in mission hack
    mentioned_in_mission = set()
    if mission:
        mission_text = "\n".join(mission)
        for _key, agent in agents_dict.items():
            if agent.get("specialist") or agent["link"] == "tool" or agent.get("expensive") or agent.get("type").startswith("image_"):
                continue
            name = agent["name"]
            if name in mentioned_in_mission:
                continue
            agent_re = re.escape(name)
            if re.search(rf"(?i)\b{agent_re}\b", mission_text):
                mentioned_in_mission.add(name)

    logger.debug("mission: %r", mentioned_in_mission)
    logger.debug("mentioned_in_mission: %r", mentioned_in_mission)
    # TODO this is a big mess, clean up

    # Filter excluded participants first
    all_participants_with_excluded: list[str] = list(set(participants(history, use_all=True) + list(mentioned_in_mission)))
    all_participants = list(set(all_participants_with_excluded) | mentioned_in_mission - EXCLUDE_PARTICIPANTS)

    # Add agents for humans in the history
    for agent in all_participants:
        agent_lc = agent.lower()
        if agent_lc not in agents_dict:
            agents_dict[agent_lc] = {
                "name": agent,
                "type": "human",
            }

    agent_names = list(agents_dict.keys())
    agents_lc = list(map(str.lower, agent_names))
    #    agents_lc_to_agents = dict(zip(agents_lc, agents_dict))
    agent_case_map = {k.lower(): agents_dict[k]["name"] for k in agents_dict}

    user = message.get("user") if message else None
    user_lc = user.lower() if user else None

    logger.debug("user, user_lc: %r %r", user, user_lc)

    if user_lc in agents_lc:
        user_agent = agents_dict[user_lc]
        logger.debug('user_agent["type"]: %r', user_agent["type"])
        if user_agent["type"] == "tool":
            invoked = who_spoke_last(history[:-1], user, agents_dict, include_self=include_self, include_humans=include_humans_for_ai_message)
            return [agent_case_map[i.lower()] for i in invoked]

    is_human = user_lc in agents_lc and agents_dict[user_lc]["type"] == "human"

    include_humans = (is_human and include_humans_for_human_message) or include_humans_for_ai_message

    if not is_human:
        include_self = False

    # Filter chat participants based on include_humans setting
    chat_participants_names_lc = [
        agent
        for agent in all_participants
        if agents_dict[agent.lower()]["type"] != "tool"
        and agents_dict[agent.lower()].get("type") != "image_a1111"
        and (include_humans or agents_dict[agent.lower()]["type"] != "human")
    ]

    # Filter chat participants based on include_humans setting
    chat_participants_names_all_lc = [
        agent
        for agent in all_participants_with_excluded
        if agents_dict[agent.lower()]["type"] != "tool"
        and agents_dict[agent.lower()].get("type") != "image_a1111"
        and (include_humans or agents_dict[agent.lower()]["type"] != "human")
    ]

    logger.debug("chat_participants_names_lc: %r", chat_participants_names_lc)

    content = message["content"] if message else ""

    # Filter out human users if requested from agent_names
    if not include_humans:
        agent_names = [name for name in agent_names if agents_dict[name]["type"] != "human"]

    agents_names_with_at = [f"@{name}" for name in agent_names]

    everyone = EVERYONE_WORDS if USE_PLURALS else []
    anyone = ANYONE_WORDS if USE_PLURALS else []
    everyone_with_at = [f"@{agent}" for agent in everyone]
    anyone_with_at = [f"@{agent}" for agent in anyone]

    if not is_human:
        everyone = random.sample(everyone, AI_EVERYONE_MAX)
        everyone_with_at = random.sample(everyone_with_at, AI_EVERYONE_MAX)

    # For @mode, all mentioned agents should reply
    invoked = who_is_named(
        content,
        f"@{user}",
        agents_names_with_at,
        include_self=include_self,
        chat_participants=chat_participants_names_lc,
        chat_participants_all=chat_participants_names_all_lc,
        everyone_words=everyone_with_at,
        anyone_words=anyone_with_at,
        get_all=True,
    )

    logger.debug("who_is_named @: %r", invoked)
    if not invoked:
        invoked = who_is_named(
            content,
            user,
            agent_names,
            include_self=include_self,
            chat_participants=chat_participants_names_lc,
            chat_participants_all=chat_participants_names_all_lc,
            everyone_words=everyone,
            anyone_words=anyone,
        )
        logger.debug("who_is_named: %r", invoked)

    direct_reply = random.random() < direct_reply_chance

    # mediators reply when no one is mentioned
    mediator = config.get("mediator")
    if mediator is None:
        mediator = []
    if not isinstance(mediator, list):
        mediator = [mediator]
#    mediator = [m for m in mediator if m != user]  # exclude user
    # We don't want mediators to reply to themselves or other mediators,
    # they need to be able to chat with users
    if user in mediator:
        mediator = []

    if not invoked and not is_human and mediator:
        invoked = [random.choice(mediator)]
        logger.debug("mediator: %r", invoked)

    if not invoked:
        logger.debug("direct_reply_chance: %r", direct_reply_chance)
        logger.debug("direct_reply: %r", direct_reply)

    if not invoked and direct_reply:
        invoked = who_spoke_last(history[:-1], user, agents_dict, include_self=include_self, include_humans=include_humans)
        logger.debug("who_spoke_last: %r", invoked)

    # If still no one to respond, default to last AI speaker or random AI
    if not invoked:
        ai_participants = [agent for agent in all_participants if agent_is_ai(agents_dict[agent.lower()])]
        ai_participants_with_excluded = [agent for agent in all_participants_with_excluded if agent_is_ai(agents_dict[agent.lower()])]
        if ai_participants and direct_reply:
            ai_participant_agents = {name.lower(): agents_dict[name.lower()] for name in ai_participants}
            invoked = who_spoke_last(history[:-1], user, ai_participant_agents, include_self=True, include_humans=False)
            logger.debug("who_spoke_last ai: %r", invoked)
        if not invoked and ai_participants and ai_participants != [user]:
            invoked = [random.choice(ai_participants)]
            logger.debug("random ai: %r", invoked)
            logger.debug("ai_participants: %r", ai_participants)
        if not invoked and ai_participants_with_excluded and ai_participants_with_excluded != [user]:
            invoked = [random.choice(ai_participants_with_excluded)]
            logger.debug("random ai 2: %r", invoked)
        if not invoked and default:
            invoked = [random.choice(default)]
            logger.debug("default: %r", invoked)

    logger.debug("who_should_respond: %r", invoked)

    # Filter out special words and only use actual agent names
    return [agent_case_map[agent.lower()] for agent in invoked if agent.lower() in agent_case_map]
