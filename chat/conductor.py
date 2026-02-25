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
from ally_agents import Agents, Agent
import ally_room
from conductor_settings import *
from settings import *
from who_is_named import *
from ally.cache import cache  # type: ignore # pylint: disable=wrong-import-order
from text import names

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


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
            return [user2.lower()]
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
        seen.add(user.lower())
        result.append(user.lower())

    return result


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
    # logger.info("history %r")
    top_dir = Path(os.environ["ALLEMANDE_ROOMS"])
    access_config = ally_room.load_config(top_dir, "access.yml")
    all_human_users = set(access_config.get("allow", []))

    # Try to find the most recent human user in the history
    for i in range(len(history) - 1, -1, -1):
        user = history[i].get("user")
        # logger.info("try user %r", user)
        if user is None:
            continue
        agent = agents.get(user)
        # logger.info("agent %r", agent)
        # logger.info("agent_is_human %r", agent and agent_is_human(agent))
        # logger.info("user in all_human_users %r", user in all_human_users)
        if agent and agent_is_human(agent):
            return user.lower()
        if not agent: #  and user in all_human_users:
            return user.lower()

    # If no human user found in history, check the room name
    if room and room.name:
        top_name = room.name.split("/")[0]
        if top_name in all_human_users:
            return top_name

    # If still no responsible human user, return None
    return None


def _apply_skip_image_replies(agents, message, history, config):
    if config.get("skip_image_replies"):
        history = [m for m in history if not is_image_message(agents, m)]
        if history:
            message = history[-1]
        else:
            message = None
            history = []
    return message, history


# def _build_agent_name_map_minimal(agents):
#     # Agent names
#     agent_names = agents.names()
#     # exclude agents without type (mix-ins) and type == "visual"
#     agent_names = [name for name in agent_names if agents.get(name).get("type") not in [None, "visual", "mixin"]]
#     # set up a map of lower-case names and aliases to canonical names
#     agent_name_map = {}
#     for k in agent_names:
#         agent = agents.get(k)
#         name = agent["name"]
#         for n in agent.get_all_names():
#             agent_name_map[n.lower()] = name
#     return agent_names, agent_name_map


# def _build_agent_name_map_full(agents):
#     # DUPLICATED CODE FROM ABOVE: preserved intentionally
#     agent_names = agents.names()
#     # exclude agents without type (mix-ins) and type == "visual"
#     agent_names = [name for name in agent_names if agents.get(name).get("type") not in [None, "visual", "mixin"]]
#     # set up a map of lower-case names and aliases to canonical names
#     agent_name_map = {}
#     agent_names_and_aliases_set = set()
#     for k in agent_names:
#         agent = agents.get(k)
#         name = agent["name"]
#         for n in agent.get_all_names():
#             agent_name_map[n.lower()] = name
#             agent_names_and_aliases_set.add(n)
#     agent_names_and_aliases = list(agent_names_and_aliases_set)
#     return agent_names, agent_name_map, agent_names_and_aliases


def _mentioned_in_mission(agents, mission, room, access_check_cache):
    mentioned_in_mission = set()
    if not mission:
        return mentioned_in_mission
    mission_text = "\n".join(mission)

    possible_mentions = names.extract_names(mission_text, at_only=True)
    for name in uniqo(possible_mentions):
        agent = agents.get(name)
        if not agent or agent.get("specialist") or agent.get("link") == "tool" or agent.get("expensive") or (agent.get("type") or "").startswith("image_"):
            continue
        mentioned_in_mission.add(name)
    mentioned_in_mission = set(filter_access(mentioned_in_mission, room, access_check_cache))
    return mentioned_in_mission


def _augment_participants_with_humans(history, mentioned_in_mission, room, access_check_cache, agents):
    # Filter excluded participants first
    all_participants_with_excluded: list[str] = list(set(participants(history, use_all=True) + list(mentioned_in_mission)))
    all_participants_with_excluded = filter_access(all_participants_with_excluded, room, access_check_cache)
    all_participants = list(set(all_participants_with_excluded) | mentioned_in_mission - EXCLUDE_PARTICIPANTS)

    # Add agents for humans in the history
    for agent in all_participants:
        if agent not in agents:
            human = Agent(data={
                "name": agent,
                "type": "human",
            }, agents=agents)
            agents.set(agent, human)

    return all_participants_with_excluded, all_participants


def _determine_user_and_flags(message, agents, include_self, include_humans_for_ai_message, include_humans_for_human_message):
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
    return user, is_human, include_humans, include_self


def _build_chat_participants_lists(all_participants_with_excluded, all_participants, agents, include_humans):
    chat_participants_names_all = []
    chat_participants_names = []
    all_participants_set = set(all_participants)
    for agent in all_participants_with_excluded:
        try:
            agent_data = agents.get(agent)
            agent_type = agent_data.get("type")
            if agent_type is None or agent_data.get("link") == "tool" or agent_type.startswith("image_") or (agent_type == "human" and not include_humans):
                continue
            chat_participants_names_all.append(agent)
            if agent in all_participants_set:
                chat_participants_names.append(agent)
        except Exception as e:
            logger.error(f"Error processing agent {agent}: {str(e)}", exc_info=True)
    return chat_participants_names_all, chat_participants_names


def _prepare_alias_lists(agents, include_humans, agent_names_and_aliases):
    if not include_humans:
        agent_names_and_aliases = [name for name in agent_names_and_aliases if agents.get(name) and agents.get(name).get("type") != "human"]
    agent_names_and_aliases_with_at = [f"@{name}" for name in agent_names_and_aliases]
    return agent_names_and_aliases, agent_names_and_aliases_with_at


def _aggregate_words(use_aggregates):
    if use_aggregates:
        everyone_with_at = [f"@{agent}" for agent in EVERYONE_WORDS]
        anyone_with_at = [f"@{agent}" for agent in ANYONE_WORDS]
        self_words_with_at = [f"@{agent}" for agent in SELF_WORDS]
    else:
        everyone_with_at = anyone_with_at = self_words_with_at = None
    return everyone_with_at, anyone_with_at, self_words_with_at


def _build_participant_aliases(chat_participants_names, agents):
    """Build list of all names/aliases for agents currently in chat"""
    participant_names = []
    for participant in chat_participants_names:
        agent = agents.get(participant)
        if agent:
            participant_names.extend(agent.get_all_names())
    return participant_names


def _setup_mediator(may_use_mediator, config, user, is_human, room, access_check_cache, everyone_except_user, everyone_except_user_all):
    use_mediator = False
    mediator = config.get("mediator")
    if mediator is None:
        mediator = []
    is_mediator = False

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

    logger.info("use_mediator: %r", use_mediator)
    logger.info("mediators: %r", mediator)
    return use_mediator, mediator, is_mediator


def _reply_chances(use_mediator, is_human, is_mediator, config):
    direct_reply_chance = 1.0
    if use_mediator:
        direct_reply_chance = config.get("direct_reply_chance", 0.0)
    direct_reply = random.random() < direct_reply_chance

    invoked_reply_chance = 1.0
    if not is_human and use_mediator and not is_mediator:
        invoked_reply_chance = config.get("ai_invoked_reply_chance", 1.0)
    invoked_reply = random.random() < invoked_reply_chance

    return direct_reply_chance, direct_reply, invoked_reply_chance, invoked_reply


def _invoke_named_at(content, user, agent_names_and_aliases_with_at, include_self, chat_participants_names, chat_participants_names_all,
                    everyone_with_at, anyone_with_at, self_words_with_at, room, access_check_cache, agents):
    reason = "named @"

    invoked = who_is_named(
        content,
        f"@{user}",
        agent_names_and_aliases_with_at,
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
        uniq=False,
    )
    logger.info("who_is_named 1 @: %r", invoked)
    invoked = filter_access(invoked, room, access_check_cache, agents)
    logger.info("who_is_named 2 @: %r", invoked)
    return reason, invoked


def _invoke_named_plain(content, user, agent_names_and_aliases, chat_participants_names, chat_participants_names_all,
                        room, access_check_cache, agents):
    reason = "named"
    invoked = who_is_named(
        content,
        user,
        agent_names_and_aliases,
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
        uniq=True,
    )
    invoked = filter_access(invoked, room, access_check_cache, agents)
    logger.debug("who_is_named: %r", invoked)
    return reason, invoked


def _direct_reply(history, user, agents, include_self, include_humans, all_participants, room, access_check_cache):
    reason = "direct_reply"
    invoked = who_spoke_last(history[:-1], user, agents, include_self=include_self, include_humans=include_humans)
    # Ensure invoked agent is in the participant list
    invoked = [agent for agent in invoked if agent in all_participants]
    invoked = filter_access(invoked, room, access_check_cache, agents)
    logger.debug("who_spoke_last: %r", invoked)
    return reason, invoked


def _mediator_pick(mediator):
    reason = "mediator"
    invoked = [random.choice(mediator)]
    logger.info("mediator: %r", invoked)
    return reason, invoked


def _compute_ai_participants(all_participants, all_participants_with_excluded, user, agents, room, access_check_cache):
    ai_participants = [agent for agent in all_participants if agent_is_ai(agents.get(agent))]
    ai_participants = filter_access(ai_participants, room, access_check_cache)
    ai_participants_with_excluded = [agent for agent in all_participants_with_excluded if agent_is_ai(agents.get(agent))]
    ai_participants_with_excluded = filter_access(ai_participants_with_excluded, room, access_check_cache)
    ai_participants_not_user = [agent for agent in ai_participants if agent != user]
    ai_participants_with_excluded_not_user = [agent for agent in ai_participants_with_excluded if agent != user]
    return ai_participants, ai_participants_with_excluded, ai_participants_not_user, ai_participants_with_excluded_not_user


def _last_ai_speaker(history, user, ai_participants, agents, room, access_check_cache):
    reason = "last_ai_speaker"
    ai_participant_agents = {name: agents.get(name) for name in ai_participants}
    invoked = who_spoke_last(history[:-1], user, ai_participant_agents, include_self=True, include_humans=False)
    invoked = filter_access(invoked, room, access_check_cache)
    logger.debug("who_spoke_last ai: %r", invoked)
    return reason, invoked


def _random_ai(ai_participants_not_user, label):
    reason = label
    invoked = [random.choice(ai_participants_not_user)]
    logger.debug("%s: %r", "random ai" if label == "random_ai" else "random ai 2", invoked)
    if label == "random_ai":
        logger.debug("ai_participants_not_user: %r", ai_participants_not_user)
    return reason, invoked


def _default_pick(default):
    reason = "default"
    invoked = [random.choice(default)]
    logger.debug("default: %r", invoked)
    return reason, invoked

def new_at_mentioned_agents(content: str, users: list[str], agent_names_and_aliases_with_at: list[str]) -> list[str]:
    """ Find new @ mentioned agents not in the existing agent names or aliases """
    # TODO
    return []

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

    logger.debug("who_should_respond 1")

    access_check_cache = {}

    logger.debug("who_should_respond: %r %r", message, history)
    if not history:
        history = []

    agents = Agents(agents.services, parent=agents)

    logger.debug("who_should_respond 2")

    if config is None:
        config = {}

    # Possibly remove image replies
    message, history = _apply_skip_image_replies(agents, message, history, config)

    logger.debug("who_should_respond 3")

    # Remove thinking sections
    history = chat.history_remove_thinking_sections(history, None)
    message = history[-1] if history else None

    logger.debug("who_should_respond 4")

    # Responsible human user
    responsible_human_user = responsible_human(history, agents, room)

    logger.debug("who_should_respond 5")

    # First pass: build minimal name map
    # agent_names, agent_name_map = _build_agent_name_map_minimal(agents)
    agent_names = agents.names()

    logger.debug("who_should_respond 6")

    # mentioned in mission
    mentioned_in_mission = _mentioned_in_mission(agents, mission, room, access_check_cache)

    logger.debug("who_should_respond 7")

    logger.debug("mission: %r", mission)
    logger.debug("mentioned_in_mission: %r", mentioned_in_mission)

    # Participants and augment with human agents if needed
    all_participants_with_excluded, all_participants = _augment_participants_with_humans(
        history, mentioned_in_mission, room, access_check_cache, agents
    )

    logger.debug("who_should_respond 8")

    # Second pass: duplicated logic preserved; now with aliases list
    # agent_names, agent_name_map, agent_names_and_aliases = _build_agent_name_map_full(agents)
    agent_names_and_aliases = agent_names  # TODO clean up

    logger.debug("who_should_respond 9")

    user = message.get("user") if message else "System"  # System ???

    is_human = False
    if user and user in agents:
        user_agent = agents.get(user)
        logger.debug('user_agent["type"]: %r', user_agent["type"])
        is_human = user_agent["type"] == "human"

    include_humans = (is_human and include_humans_for_human_message) or include_humans_for_ai_message

    logger.debug("who_should_respond 10")

    # TODO AIs talk to themselves?  not right now
    if not is_human:
        include_self = False

    # Build chat participants lists
    chat_participants_names_all, chat_participants_names = _build_chat_participants_lists(
        all_participants_with_excluded, all_participants, agents, include_humans
    )
    logger.debug("chat_participants_names: %r", chat_participants_names)

    logger.debug("who_should_respond 11")

    content = message["content"] if message else ""

    # Filter out human users if requested from agent_names
    agent_names_and_aliases_with_at = [f"@{name}" for name in agent_names_and_aliases]
    # agent_names_and_aliases, agent_names_and_aliases_with_at = _prepare_alias_lists(agents, not not include_humans, agent_names_and_aliases)

    # logger.debug("agent_names: %r", agent_names)

    logger.debug("who_should_respond 12")

    everyone_with_at, anyone_with_at, self_words_with_at = _aggregate_words(use_aggregates)

    logger.debug("who_should_respond 13")

    # Build names/aliases for participants only (for non-@ mentions)
    participant_names_and_aliases = _build_participant_aliases(chat_participants_names, agents)
    logger.debug("participant_names_and_aliases: %r", participant_names_and_aliases)

    # When starting a clean chat, allow to invoke without @ mentions
    if len(history) > 1:
        names_and_aliases = participant_names_and_aliases
    else:
        names_and_aliases = agent_names_and_aliases

    logger.debug("who_should_respond 14")

    # Calculate everyone_except_user lists
    everyone_except_user = [a for a in chat_participants_names if a != user]
    everyone_except_user_all = [a for a in chat_participants_names_all if a != user]

    logger.debug("who_should_respond 15")

    # Mediator setup
    use_mediator, mediator, is_mediator = _setup_mediator(
        may_use_mediator, config, user, is_human, room, access_check_cache, 
        everyone_except_user, everyone_except_user_all
    )

    # direct_reply_chance and invoked_reply_chance
    direct_reply_chance, direct_reply, invoked_reply_chance, invoked_reply = _reply_chances(
        use_mediator, is_human, is_mediator, config
    )

    logger.debug("who_should_respond 16")

    reason = None
    invoked = None

    # For @mode, all mentioned agents should reply
    reason, invoked = _invoke_named_at(
        content, user, agent_names_and_aliases_with_at, include_self,
        chat_participants_names, chat_participants_names_all,
        everyone_with_at, anyone_with_at, self_words_with_at,
        room, access_check_cache, agents,
    )

    logger.debug("who_should_respond 17")

    # If we @ mention someone not present, no one should respond
    at_mention_present = chat.has_at_mention(content)
    if not invoked and at_mention_present:
        # if AUTO_CREATE_UNKNOWN_AGENTS:
        #     users = cache.load(str(PATH_USERS)).strip().split("\n")
        #     new_agents = new_at_mentioned_agents(content, users, agent_names_and_aliases_with_at)
        #     if new_agents:
        #         return responsible_human_user, [AUTO_CREATE_UNKNOWN_AGENTS]
        return responsible_human_user, []

    if not invoked and at_only:
        invoked = ["-None-"]

    logger.debug("who_should_respond 18")

    if not invoked:
        reason, invoked = _invoke_named_plain(
            content, user, names_and_aliases, chat_participants_names, chat_participants_names_all,
            room, access_check_cache, agents,
        )
        # if ai_invoked_reply_chance failed, the AI can only invoke tools
        if not invoked_reply:
            invoked = [agent for agent in invoked if agent_is_tool(agents.get(agent))]

    if not invoked:
        logger.info("direct_reply_chance: %r", direct_reply_chance)
        logger.info("direct_reply: %r", direct_reply)

    logger.debug("who_should_respond 19")

    # direct replies: Allow replying to self without triggering an AI to respond
    if not invoked and direct_reply:
        reason, invoked = _direct_reply(
            history, user, agents, include_self, include_humans, all_participants, room, access_check_cache,
        )

    logger.debug("who_should_respond 20")

    # mediator
    if not invoked and use_mediator:
        reason, invoked = _mediator_pick(mediator)

    # If still no one to respond, default to last AI speaker
    ai_participants = ai_participants_with_excluded = ai_participants_not_user = ai_participants_with_excluded_not_user = []
    if not invoked:
        ai_participants, ai_participants_with_excluded, ai_participants_not_user, ai_participants_with_excluded_not_user = _compute_ai_participants(
            all_participants, all_participants_with_excluded, user, agents, room, access_check_cache,
        )
        default = filter_access(default, room, access_check_cache)
        if ai_participants and direct_reply:
            reason, invoked = _last_ai_speaker(history, user, ai_participants, agents, room, access_check_cache)

    logger.debug("who_should_respond 21")

    # mediator is better than random!
    if not invoked and may_use_mediator and mediator:
        reason, invoked = _mediator_pick(mediator)

    # random AI
    if not invoked and ai_participants_not_user:
        reason, invoked = _random_ai(ai_participants_not_user, "random_ai")
    if not invoked and ai_participants_with_excluded_not_user:
        reason, invoked = _random_ai(ai_participants_with_excluded_not_user, "random_ai_with_excluded")
    if not invoked and default:
        reason, invoked = _default_pick(default)

    logger.debug("who_should_respond 22")

    # Final filtering to canonical agent names
    agents_to_respond = filter_access(invoked, room, access_check_cache, agents)

    logger.debug("who_should_respond 23")

    logger.info("who_should_respond: %r %r", reason, agents_to_respond)
    for agent in agents_to_respond:
        agent_data = agents.get(agent)
        agent_type = agent_data.get("type")
        logger.info("  %s: %s", agent, agent_type)

    logger.debug("who_should_respond 24")

    return responsible_human_user, agents_to_respond
