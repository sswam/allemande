#!/usr/bin/env python3-allemande

""" conductor.py: decide which agent/s should respond to a message """

import os
import logging
import re
import random
from typing import Any, Iterable
from pathlib import Path

import chat
from util import uniqo
from agents import Agents, Agent
import ally_room

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# The EVERYONE_WORDS and ANYONE_WORDS now only work with @ prefix, so we can include more words

IGNORE_CASE = False

EVERYONE_WORDS = [
    # General plural addresses
    "everyone",
    "everybody",
    "all",
    "girls",
    "boys",
    "ladies",
    "gentlemen",
    "men",
    "women",
    "folks",
    "y'all",
    "you all",
    "all of you",
    "gang", "crew", "team",
]

ANYONE_WORDS = [
    "anyone",
    "someone",
    "who",
    "anybody",
    "somebody",
    "another",
    "other",

    # "one of you",
    # "one of y'all",
    # "who's next",
    # "who's up next",
    # "who's ready",
    # "who's going to",
    # "who is next",
    # "who is ready",
    # "who is going",
    # "who wants to",
    # "who else",
]

SELF_WORDS = ["self", "me", "himself", "herself"]

# TODO configureable by room

# TODO exclude based on an attribute or settings
# TODO should not include tools in the list of participants
EXCLUDE_TOOLS = set(["Palc", "Dogu", "Gido", "Lary", "Matz", "Luah", "Jyan", "Jahl", "Faby", "Qell", "Bilda", "Goog", "Gimg", "Utube", "Pr0nto"])
EXCLUDE_PARTICIPANTS = set(["System", "Sia", "Nova", "Pixi", "Brie", "Chaz", "Atla", "Pliny", "Morf"])
# EXCLUDE_PARTICIPANTS = set(["System", "Palc", "Dogu", "Gid", "Lary", "Matz", "Luah", "Jyan", "Jahl", "Faby", "Qell", "Bilda"])
EXCLUDE_PARTICIPANTS_SYSTEM = set(["System", "The Cast"])

EVERYONE_MAX = 5
AI_EVERYONE_MAX = 2

USE_PLURALS = True


def find_name_in_content(content: str, name: str, ignore_case: bool = True, is_tool: bool = False) -> tuple[int, int, int, str | None] | None:
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
    start_comma_word = r"^\s*" + re.escape(name) + r"\b\s*(,|$)"  # at start with comma, or whole line

    patterns = [start_comma_word]

    if not is_tool:
        comma_word_end = r",\s*" + re.escape(name) + r"\b\s*\W*$"  # at end with comma
        word_start = r"^\s*" + re.escape(name) + r"\b"  # at start
        word_end = r"(\W|\b|^)" + re.escape(name) + r"\b\s*[\.!?]?\s*$"  # at end
        whole_word = r"(\W|\b|^)" + re.escape(name) + r"\b"  # anywhere
        patterns += [comma_word_end, word_start, word_end, whole_word]

    flags = re.IGNORECASE if ignore_case else 0

    # Split into sentences
    best_match = (100, -1, len(content), 0, "")  # (match_type, sentence_num, position, length, name)

    length = len(name)

    sentences = re.split(r'[.!?\n]+', content)
    for sent_num, sentence in enumerate(reversed(sentences)):  # reverse to prioritize later sentences
        for match_type, pattern in enumerate(patterns):
            if match := re.search(pattern, sentence, flags):
                # Calculate absolute position in original content
                abs_pos = content.find(sentence) + match.start()
                current_match = (match_type, sent_num, abs_pos, -length, name)
                best_match = min(best_match, current_match)

    if best_match[4]:
        return best_match
    return None


def who_is_named(
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

    logger.debug(
        "who_is_named: %r %r %r %r %r %r %r %r %r %r", content, user, agent_names, include_self, chat_participants, chat_participants_all, everyone_words, anyone_words, self_words, get_all
    )

    # Calculate everyone_except_user
    everyone_except_user = [a for a in chat_participants if a != user]
    everyone_except_user_all = [a for a in chat_participants_all if a != user]

    agents_and_plurals = agent_names
    if USE_PLURALS:
        agents_and_plurals = agent_names + everyone_words + anyone_words + self_words

    matches = []
    for agent in agents_and_plurals:
        is_tool = agents is not None and agent in agents and agent_is_tool(agents.get(agent))
        best_match = find_name_in_content(content, agent, is_tool=is_tool, ignore_case=ignore_case)
        if best_match:
            matches.append(best_match)

    if not include_self and user:
        matches = [m for m in matches if m[4] and m[4] != user]
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
    for _type, _sentence, _pos, length, agent in matches:
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
            if filter_access([agent], room, access_check_cache):
                result.append(agent)

    result = [x.lstrip("@") for x in result]
    result = uniqo(result)

    logger.debug("who_is_named result: %r", result)

    return result


def who_spoke_last(
    history: list[dict[str, Any]],
    user: str,
    agents: Agents,
    include_self: bool = False,
    include_humans: bool = True,
    include_tools: bool = False,
) -> list[str]:
    """check who else spoke in recent history"""
    for i in range(len(history) - 1, -1, -1):
        user2 = history[i].get("user")
        if user2 is None:
            continue
        if user2 in EXCLUDE_PARTICIPANTS_SYSTEM:
            continue
        if (
            user2 in agents
            and (include_self or user2 != user)
            and (include_tools or not agent_is_tool(agents.get(user2)))
            and (include_humans or not agent_is_human(agents.get(user2)))
        ):
            return [user2]
    return []


def participants(history: list[dict[str, str]], use_all=False) -> list[str]:
    """get all participants in the history"""
    agents_set = set(x["user"] for x in history if x.get("user"))
    agents_set -= EXCLUDE_PARTICIPANTS_SYSTEM
    agents_set -= EXCLUDE_TOOLS
    if not use_all:
        agents_set -= EXCLUDE_PARTICIPANTS
    return list(agents_set)


def get_all_participants(history: list[dict[str, str]]) -> list[str]:
    """get all participants in the history including system and tools, most recent first"""
    seen = set()
    result = []

    # Go through history in reverse to get most recent first
    for msg in reversed(history):
        user = msg.get("user")
        if not user or user in seen:
            continue
        seen.add(user)
        result.append(user)

    return result


def agent_is_tool(agent: dict[str, Any]) -> bool:
    """check if an agent is a tool"""
    return agent.get("link") == "tool" or agent.get("type").startswith("image_")


def agent_is_human(agent: dict[str, Any]) -> bool:
    """check if an agent is a human"""
    return agent.get("type") == "human"


def agent_is_ai(agent: dict[str, Any]) -> bool:
    """check if an agent is an AI"""
    return not agent_is_tool(agent) and not agent_is_human(agent)


def is_image_message(agents: Agents, message: dict[str, str]) -> bool:
    """check if a message is an image message"""
    user = message.get("user")
    if not user:
        return False
    agent = agents.get(user)
    if not agent:
        return False
    service = agent.get("type")
    return service and service.startswith("image_")


def responsible_human(
    history: list[dict[str, Any]],
    agents: Agents,
    room: chat.Room | None = None,
) -> str | None:
    """returns guess at responsible human user"""
    # TODO
    # responsible human user is based on the most recent message from a human in the chat history (from the end)
    # or, if none, the top-level path component of the room name, if it matches a user's name  (e.g. sam/foo -> sam and sam -> sam)
    top_dir = Path(os.environ["ALLEMANDE_ROOMS"])
    access_config = ally_room.load_config(top_dir, "access.yml")
    all_human_users = set(access_config.get("allow", []))

    # Try to find the most recent human user in the history
    for i in range(len(history) - 1, -1, -1):
        user = history[i].get("user")
        if user is None:
            continue
        agent = agents.get(user)
        if agent and agent_is_human(agent):
            return user.lower()
        if not agent and user in all_human_users:
            return user.lower()

    # If no human user found in history, check the room name
    if room and room.name:
        top_name = room.name.split("/")[0]
        if top_name in all_human_users:
            return top_name

    # If still no responsible human user, return None
    return None


def who_should_respond(
    message: dict[str, Any] | None,
    agents: Agents | None = None,
    history: list[dict[str, Any]] | None = None,
    default: list[str] | None = None,
    include_self: bool = True,
    include_humans_for_ai_message: bool = True,
    include_humans_for_human_message: bool = True,
    may_use_mediator: bool = True,
    config: dict[str, Any] | None = None,
    mission: str | None = None,
    room: chat.Room | None = None,
    at_only: bool = False,
    use_aggregates: bool = True,
) -> tuple[str|None, list[str]]:
    """returns guess at responsible human user, and who should respond to a message"""

    access_check_cache = {}

    logger.debug("who_should_respond: %r %r", message, history)
    if not history:
        history = []

    agents = Agents(agents.services, parent=agents)

    if config is None:
        config = {}

    if config.get("skip_image_replies"):
        history = [m for m in history if not is_image_message(agents, m)]
        if history:
            message = history[-1]
        else:
            message = None
            history = []

    history = chat.history_remove_thinking_sections(history, None)

    # mentioned in mission hack
    mentioned_in_mission = set()
    if mission:
        mission_text = "\n".join(mission)
        for _key, agent in agents.items():
            if agent.get("specialist") or agent.get("link") == "tool" or agent.get("expensive") or (agent.get("type") or "").startswith("image_"):
                continue
            name = agent["name"]
            if name in mentioned_in_mission:
                continue
            agent_re = re.escape(name)
            if re.search(rf"(?i)\b{agent_re}\b", mission_text):
                mentioned_in_mission.add(name)

    mentioned_in_mission = set(filter_access(mentioned_in_mission, room, access_check_cache))

    logger.debug("mission: %r", mission)
    logger.debug("mentioned_in_mission: %r", mentioned_in_mission)
    # TODO this is a big mess, clean up

    # Filter excluded participants first
    all_participants_with_excluded: list[str] = list(set(participants(history, use_all=True) + list(mentioned_in_mission)))
    all_participants_with_excluded = filter_access(all_participants_with_excluded, room, access_check_cache)
    all_participants = list(set(all_participants_with_excluded) | mentioned_in_mission - EXCLUDE_PARTICIPANTS)

    logger.debug("all_participants: %r", all_participants)
    logger.debug("all_participants_with_excluded: %r", all_participants_with_excluded)

    logger.debug("agent_names: %r", agents.names())

    # Add agents for humans in the history
    for agent in all_participants:
        if agent not in agents:
            human = Agent(data={
                "name": agent,
                "type": "human",
            }, agents=agents)
            agents.set(agent, human)

    agent_names = agents.names()
    agent_case_map = {k.lower(): agents.get(k)["name"] for k in agent_names}

    user = message.get("user") if message else "System"  # System ???

    is_human = False

    if user in agents:
        user_agent = agents.get(user)
        logger.debug('user_agent["type"]: %r', user_agent["type"])
        is_human = user_agent["type"] == "human"

    include_humans = (is_human and include_humans_for_human_message) or include_humans_for_ai_message

    # TODO AIs talk to themselves?  not right now
    if not is_human:
        include_self = False

    # Filter chat participants based on include_humans setting
    chat_participants_names = [
        agent
        for agent in all_participants
        if agents.get(agent)["type"] != "tool" and not agents.get(agent)["type"].startswith("image_")
        and (include_humans or agents.get(agent)["type"] != "human")
    ]

    # Filter chat participants based on include_humans setting
    chat_participants_names_all = [
        agent
        for agent in all_participants_with_excluded
        if agents.get(agent)["type"] != "tool" and not agents.get(agent)["type"].startswith("image_")
        and (include_humans or agents.get(agent)["type"] != "human")
    ]

    logger.debug("chat_participants_names: %r", chat_participants_names)

    content = message["content"] if message else ""

    # Filter out human users if requested from agent_names
    if not include_humans:
        agent_names = [name for name in agent_names if agents.get(name)["type"] != "human"]

    agent_names_with_at = [f"@{name}" for name in agent_names]

    logger.debug("agent_names: %r", agent_names)

    if use_aggregates:
        everyone_with_at = [f"@{agent}" for agent in EVERYONE_WORDS]
        anyone_with_at = [f"@{agent}" for agent in ANYONE_WORDS]
        self_words_with_at = [f"@{agent}" for agent in SELF_WORDS]
    else:
        everyone_with_at = anyone_with_at = self_words_with_at = None

    # Calculate everyone_except_user
    everyone_except_user = [a for a in chat_participants_names if a != user]
    everyone_except_user_all = [a for a in chat_participants_names_all if a != user]

    # mediators reply when no one is mentioned, and no direct reply
    use_mediator = False
    mediator = config.get("mediator")
    if mediator is None:
        mediator = []

    if may_use_mediator:
        mediator_for_humans = config.get("mediator_for_humans", False)
        if not isinstance(mediator, list):
            mediator = [mediator]
        mediator = mediator.copy()
        for i, agent in enumerate(mediator):
            if agent in ANYONE_WORDS and everyone_except_user:
                mediator[i] = random.choice(everyone_except_user)
            elif agent in ANYONE_WORDS and everyone_except_user_all:
                mediator[i] = random.choice(everyone_except_user_all)
        mediator = filter_access(mediator, room, access_check_cache)

        is_mediator = user in mediator

        # We don't want mediators to reply to themselves
        mediator = [m for m in mediator if m != user]

        use_mediator = mediator and (mediator_for_humans or not is_human)

    logger.debug("use_mediator: %r", use_mediator)
    logger.debug("mediators: %r", mediator)

    # direct_reply_chance
    direct_reply_chance = 1.0
    if use_mediator:
        direct_reply_chance = config.get("direct_reply_chance", 0.0)

    direct_reply = random.random() < direct_reply_chance

    # AI invoked reply chance
    # The randomness prevents interminable loops between two AIs.
    # At the moment, only enabled when a mediator is used.
    # Exceptions:
    # - humans invoking anyone
    # - mediators invoking anyone
    # - AIs invoking tools (e.g. AI art)
    # - @ mentions
    invoked_reply_chance = 1.0
    if not is_human and use_mediator and not is_mediator:
        invoked_reply_chance = config.get("ai_invoked_reply_chance", 1.0)

    invoked_reply = random.random() < invoked_reply_chance

    reason = None
    invoked = None

    # For @mode, all mentioned agents should reply
    # To start talking to self, must use @name now.
    reason = "named @"
    invoked = who_is_named(
        content,
        f"@{user}",
        agent_names_with_at,
        include_self=include_self,
        chat_participants=chat_participants_names,
        chat_participants_all=chat_participants_names_all,
        everyone_words=everyone_with_at,
        anyone_words=anyone_with_at,
        self_words=self_words_with_at,
        get_all=True,
        room=room,
        access_check_cache=access_check_cache,
        agents=agents,
        ignore_case=True,
    )
    invoked = filter_access(invoked, room, access_check_cache)
    logger.debug("who_is_named @: %r", invoked)

    if not invoked and at_only:
        invoked = ["-None-"]

    if not invoked:
        reason = "named"
        invoked = who_is_named(
            content,
            user,
            agent_names,
            include_self=False,  # no talking to self without @ now
            chat_participants=chat_participants_names,
            chat_participants_all=chat_participants_names_all,
            everyone_words=None,
            anyone_words=None,
            self_words=None,
            room=room,
            access_check_cache=access_check_cache,
            agents=agents,
            ignore_case=False,
        )
        invoked = filter_access(invoked, room, access_check_cache)
        logger.debug("who_is_named: %r", invoked)

        # if ai_invoked_reply_chance failed, the AI can only invoke tools
        if not invoked_reply:
            invoked = [agent for agent in invoked if agent_is_tool(agents.get(agent))]

    if not invoked:
        logger.info("direct_reply_chance: %r", direct_reply_chance)
        logger.info("direct_reply: %r", direct_reply)

    # direct replies: Allow replying to self without triggering an AI to respond
    if not invoked and direct_reply:
        reason = "direct_reply"
        invoked = who_spoke_last(history[:-1], user, agents, include_self=include_self, include_humans=include_humans)

        # Ensure invoked agent is in the participant list
        invoked = [agent for agent in invoked if agent in all_participants]

        invoked = filter_access(invoked, room, access_check_cache)
        logger.debug("who_spoke_last: %r", invoked)

    # mediator
    if not invoked and use_mediator:
        reason = "mediator"
        invoked = [random.choice(mediator)]
        logger.info("mediator: %r", invoked)

    # If still no one to respond, default to last AI speaker
    if not invoked:
        ai_participants = [agent for agent in all_participants if agent_is_ai(agents.get(agent))]
        ai_participants = filter_access(ai_participants, room, access_check_cache)
        ai_participants_with_excluded = [agent for agent in all_participants_with_excluded if agent_is_ai(agents.get(agent))]
        ai_participants_with_excluded = filter_access(ai_participants_with_excluded, room, access_check_cache)
        default = filter_access(default, room, access_check_cache)
        if ai_participants and direct_reply:
            reason = "last_ai_speaker"
            ai_participant_agents = {name: agents.get(name) for name in ai_participants}
            invoked = who_spoke_last(history[:-1], user, ai_participant_agents, include_self=True, include_humans=False)
            invoked = filter_access(invoked, room, access_check_cache)
            logger.debug("who_spoke_last ai: %r", invoked)
        ai_participants_not_user = [agent for agent in ai_participants if agent != user]
        ai_participants_with_excluded_not_user = [agent for agent in ai_participants_with_excluded if agent != user]

    # mediator is better than random!
    if not invoked and may_use_mediator and mediator:
        reason = "mediator"
        invoked = [random.choice(mediator)]
        logger.info("mediator: %r", invoked)

    # random AI
    if not invoked and ai_participants_not_user:
        reason = "random_ai"
        invoked = [random.choice(ai_participants_not_user)]
        logger.debug("random ai: %r", invoked)
        logger.debug("ai_participants_not_user: %r", ai_participants_not_user)
    if not invoked and ai_participants_with_excluded_not_user:
        reason = "random_ai_with_excluded"
        invoked = [random.choice(ai_participants_with_excluded_not_user)]
        logger.debug("random ai 2: %r", invoked)
    if not invoked and default:
        reason = "default"
        invoked = [random.choice(default)]
        logger.debug("default: %r", invoked)

    logger.info("who_should_respond: %r %r", reason, invoked)

    # Filter out special words and only use actual agent names
    agents_to_respond = [agent_case_map[agent.lower()] for agent in invoked if agent.lower() in agent_case_map]

    # Responsible human user
    responsible_human_user = responsible_human(history, agents, room)

    return responsible_human_user, agents_to_respond


def filter_access(invoked: Iterable[str], room: chat.Room | None, access_check_cache: dict[str, int]) -> list[str]:
    """filter out agents that don't have access"""
    if not room:
        return list(invoked)
    result = []
    for agent in invoked:
        agent = re.sub(r"^@", "", agent)
        if access_check_cache.get(agent) is None:
            access_check_cache[agent] = room.check_access(agent).value
        if access_check_cache[agent] & chat.Access.READ_WRITE.value:
            result.append(agent)
    return result
