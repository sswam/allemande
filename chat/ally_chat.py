#!/usr/bin/env python3-allemande
# pylint: disable=unused-argument

""" Ally Chat / Electric Barbarella v1.1.0 - multi-user AI chat app """

import os
import sys
import argparse
import logging
from pathlib import Path
import re
import asyncio
from collections import defaultdict
import json
from typing import Any
import aiohttp
from urllib.parse import urlparse, quote
import random
import importlib

import requests
import shlex
from watchfiles import awatch, Change
import yaml
import regex
from num2words import num2words

import atail  # type: ignore
import ucm  # type: ignore
import conductor
import search  # type: ignore
import tab  # type: ignore
import chat
import bb_lib
import ally_markdown
import ally_room
import fetch
import llm  # type: ignore
import ally_agents
import remote_agents
import local_agents
import util
import tasks
import ally
import settings


RELOADABLE_MODULES = [
    "atail", "ucm", "conductor", "search", "tab", "chat", "bb_lib",
    "ally_markdown", "ally_room", "fetch", "llm", "ally_agents", "remote_agents",
    "local_agents", "util", "tasks", "ally", "settings"
]


logger = logging.getLogger(__name__)
logging.getLogger('watchfiles').setLevel(logging.WARNING)

Messasge = dict[str, Any]


def summary_read(file, args):
    """Read summary from a file."""
    text = ""
    if file and os.path.exists(file):
        with open(file, encoding="utf-8") as f:
            text = f.read()
    # Indent it all and put Summary: at the start
    if text:
        text = "Summary:" + re.sub(r"^", "\t", text, flags=re.MULTILINE)
        lines = text.split(args.delim)
    else:
        lines = []
    return lines


def config_read(file):
    """Read a YAML config file."""
    if file and os.path.exists(file):
        with open(file, encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


async def run_search(agent, query, file, args, history, history_start, limit=True, mission=None, summary=None, config=None, num=10, agents=None, responsible_human: str=None):
    """Run a search agent."""
    # NOTE: responsible_human is not used here yet
    name = agent.name
    engine_id = agent.get("id", name)
    logger.debug("history: %r", history)
    history_messages = list(bb_lib.lines_to_messages(history))
    logger.debug("history_messages: %r", history_messages)
    message = history_messages[-1]
    query = message["content"]

    logger.debug("query 0: %r", query)

    query = chat.clean_prompt([query], name, args.delim) + "\n"

    logger.debug("query 1: %r", query)
    # query = query.split("\n")[0]
    # logger.debug("query 2: %r", query)
    # rx = r'((ok|okay|hey|hi|ho|yo|hello|hola)\s)*\b'+re.escape(name)+r'\b'
    # rx = r".*?\b" + re.escape(name) + r"\b"
    # logger.debug("rx: %r", rx)
    # query = re.sub(rx, "", query, flags=re.IGNORECASE | re.DOTALL)
    # logger.debug("query 3: %r", query)
    query = re.sub(r"^(show me|search( for|up)?|find( me)?|look( for| up)?|what(\'s| is) (the|a|an)?)\s+", "", query, flags=re.IGNORECASE)
    logger.debug("query 4: %r", query)
    # query = re.sub(r"#.*", "", query)
    # logger.debug("query 5: %r", query)
    # query = re.sub(r"[^\x00-~]", "", query)  # filter out emojis
    # logger.debug("query 6: %r", query)
    # query = re.sub(r"^\s*[,;.]|[,;.]\s*$", "", query).strip()

    logger.debug("query: %r %r", engine_id, query)

    try:
        response = await search.search(query, engine=engine_id, markdown=True, num=num, limit=limit, safe=not settings.ADULT)
    except requests.exceptions.HTTPError:
        if name != "Pr0nto":
            raise
        query2 = ally.stopwords.strip_stopwords(query, strict=True)
        logger.info("Stripped stopwords from query: %r -> %r", query, query2)
        response = await search.search(query2, engine=engine_id, markdown=True, num=num, limit=limit, safe=not settings.ADULT)

    response2 = f"{name}:\t\n{response}"
    logger.debug("response:\n%s", response2)
    response3 = chat.fix_response_layout(response2, args, agent)
    logger.debug("response3:\n%s", response3)

    # wrap in a <div class="search"> container if not in a div already
    if re.search(r"<div\b", response3):
        response4 = re.sub(r"<div\b", r'<div class="search"', response3, flags=re.IGNORECASE, count=1)
    else:
        response4 = re.sub(r"\t\n(.*)", rf'\t\n\t<div class="search" markdown="1">\n\1\n\t</div>\n', response3, flags=re.DOTALL, count=1)

#     # wrap secondary divs in <details>
#     response4 = re.sub(
#         r"(</div>\n?\s*)(<div\b.*)",
#         r"""\1<details class="search"><summary>more</summary>\n\t\2</details>\n""",
#         response3,
#         flags=re.DOTALL,
#     )

#     # wrap div results in <details>, replacing outer div
#     response4 = re.sub(
#         r"<div>(.*)</div>",
#         r"""<details class="search"><summary>more</summary>\1</details>""",
#         response3,
#         flags=re.DOTALL,
#     )
#
#     logger.info("response4:\n%s", response4)

    return response4


def load_local_agents(room, agents=None):
    """Load the local agents."""
    room_dir = room.parent
    top_dir = settings.PATH_ROOMS
    if top_dir != room_dir and top_dir not in room_dir.parents:
        raise ValueError(f"Room directory {room_dir} is not under {top_dir}")

    agents_dirs = []

    while True:
        if room_dir == top_dir:
            break
        agents_dir = room_dir / "agents"
        if agents_dir.exists():
            agents_dirs.append(agents_dir)
        room_dir = room_dir.parent

    # logger.info("Loading local agents for room %r from %r", room.path, agents_dirs)

    for agent_dir in reversed(agents_dirs):
        agents = ally_agents.Agents(services, parent=agents)
        agents.load(agent_dir, visual=False)

        agents.write_agents_list(agent_dir.parent / ".agents.yml")

        logger.info("Loaded agents from %s", agent_dir)
        logger.debug("Agents: %r", agents.names())

    return agents


# def filter_agents_with_access(room, agents):
#     """Filter agents with access to this room."""
#     agents = ally_agents.Agents(agents.services, parent=agents)
#     for agent in agents.values():
#         # TODO should check all aliases; re-think how aliases work
#         if room.check_access(agent.name).value & ally_room.Access.READ_WRITE.value != ally_room.Access.READ_WRITE.value:
#             logger.info("Removing agent %s without access to room %s", agent.name, room.path)
#             agents.set(agent.name, None)
#     return agents


async def process_file(file, args, history_start=0, skip=None, agents=None, poke=False) -> int:
    """Process a file, return True if appended new content."""
    logger.info("Processing %s", file)

    room = ally_room.Room(path=Path(file))
    history = chat.chat_read(file, args)
    config = load_config(room)
    mission = load_mission(room, config, args)
    summary = load_summary(room, args)
    agents = load_local_agents(room, agents)

    history_messages = list(bb_lib.lines_to_messages(history))

    if should_skip_editing_command(history_messages, poke):
        return 0

    last_message_id = len(history_messages) - 1

    history_messages = chat.apply_editing_commands(history_messages)
    history = list(bb_lib.messages_to_lines(history_messages))
    message = history_messages[-1] if history_messages else None

    bots, responsible_human = determine_responders(message, agents, history_messages, config, room, mission, poke)
    logger.info("who should respond: %r; responsible: %r", bots, responsible_human)

    message, history, history_messages = handle_directed_poke(message, history, history_messages, file, args, last_message_id)

    count = await process_bot_responses(
        bots, agents, file, args, history, history_start, mission,
        summary, config, responsible_human, poke, skip, room
    )
    return count


def load_config(room):
    """Load and return configuration from room."""
    config_file = room.find_resource_file("yml", "options")
    logger.debug("config_file: %r", config_file)
    config = config_read(config_file)
    logger.debug("config: %r", config)
    return config


def load_mission(room, config, args):
    """Load and return mission from room."""
    mission_file_name = config.get("mission", "mission")
    mission_try_room_name = "mission" not in config
    mission_file = room.find_resource_file("m", mission_file_name, try_room_name=mission_try_room_name)
    return chat.chat_read(mission_file, args)


def load_summary(room, args):
    """Load and return summary from room."""
    summary_file = room.find_resource_file("s", "summary")
    return summary_read(summary_file, args)


def should_skip_editing_command(history_messages, poke):
    """Check if we should skip processing due to editing command."""
    if not history_messages or poke:
        return False
    message = history_messages[-1]
    return message and re.search(r"""<ac\b[a-z0-9 ="']*>\s*$""", message["content"], flags=re.IGNORECASE)


def handle_directed_poke(message, history, history_messages, file, args, last_message_id):
    """Handle soft undo for directed-poke commands."""
    if not message or not message["content"].startswith("-@"):
        return message, history, history_messages

    undo_message = f"{message['user']}:\t<ac rm={last_message_id}>"
    history_messages.pop()
    history.pop()
    chat.chat_write(file, [undo_message], delim=args.delim, invitation=args.delim)
    message = history_messages[-1] if history_messages else None
    return message, history, history_messages


def determine_responders(message, agents, history_messages, config, room, mission, poke):
    """Determine which bots and humans should respond."""
    welcome_agents = [name for name, agent in agents.items() if agent.get("welcome")]
    include_self = config.get("self_talk", True) and not poke

    responsible_human, bots = conductor.who_should_respond(
        message, agents=agents, history=history_messages, default=welcome_agents,
        include_humans_for_ai_message=not poke, include_humans_for_human_message=not poke,
        mission=mission, config=config, room=room, include_self=include_self,
    )
    return bots, responsible_human


async def process_bot_responses(bots, agents, file, args, history, history_start,
                                mission, summary, config, responsible_human, poke, skip, room):
    """Process responses from all bots."""
    count = 0
    for bot in bots:
        if not should_process_bot(bot, agents):
            continue

        response = await generate_bot_response(
            bot, agents, file, args, history, history_start,
            mission, summary, config, responsible_human, room
        )

        if response is None:
            continue

        response = response.lstrip().rstrip("\n ")
        agent = agents.get(bot)
        response = await handle_forwarding(response, agent, agents, file, args, history,
                                        history_start, mission, summary, config, responsible_human, room)

        response = apply_narrator_mode(response, agent)
        poke_next = should_poke_next(response, agent)

        history.append(response)
        update_skip_tracking(poke_next, skip, file)
        chat.chat_write(file, history[-1:], delim=args.delim, invitation=args.delim)
        count += 1

    return count


def should_process_bot(bot, agents):
    """Check if bot should be processed."""
    if not (bot and bot in agents.names()):
        return False
    agent = agents.get(bot)
    return agent.get("type") not in [None, "human", "visual", "mixin"]


async def generate_bot_response(bot, agents, file, args, history, history_start,
                                mission, summary, config, responsible_human, room):
    """Generate a response from a bot agent."""
    agent = agents.get(bot)
    my_mission = load_agent_mission(room, bot, mission, args, agent=agent)
    query, history = prepare_query(history, agent, bot)

    return await run_agent(
        agent, query, file, args, history, history_start=history_start,
        mission=my_mission, summary=summary, config=config,
        agents=agents, responsible_human=responsible_human
    )


def load_agent_mission(room, bot, base_mission, args, agent=None):
    """Load agent-specific mission/s and merge with base mission."""
    my_mission = base_mission.copy()
    agent_mission_file = room.find_agent_resource_file("m", bot)
    mission2 = None
    if agent:
        agent_mission2 = agent.get("mission")
        if agent_mission2:
            agent_mission_file2 = room.find_resource_file("m", agent_mission2, try_room_name=False)
            mission2 = chat.chat_read(agent_mission_file2, args)
    mission3 = chat.chat_read(agent_mission_file, args)
    logger.debug("mission: %r", base_mission)
    logger.debug("mission2: %r", mission2)
    logger.debug("mission3: %r", mission3)
    if mission2:
        my_mission += [""] + mission2
    if mission3:
        my_mission += [""] + mission3
    return my_mission


def prepare_query(history, agent, bot):
    """Prepare query and history for agent."""
    if history:
        query1 = history[-1]
    else:
        query1 = agent.get("starter_prompt", STARTER_PROMPT) or ""
        query1 = query1.format(bot=bot) or None
        history = [query1]

    logger.debug("query1: %r", query1)
    messages = list(bb_lib.lines_to_messages([query1]))
    query = messages[-1]["content"] if messages else None
    logger.debug("query: %r", query)
    return query, history


async def handle_forwarding(response, agent, agents, file, args, history,
                        history_start, mission, summary, config, responsible_human, room):
    """Handle forwarding logic for agent responses."""
    if not agent.get("forward"):
        return response

    response = apply_forward_triggers(response, agent)

    if not response:
        return response

    forward_target = determine_forward_target(response, agent, agents, config, room)

    if not forward_target:
        return response

    return await execute_forward(forward_target, agent, agents, file, args, history,
                                history_start, mission, summary, config, responsible_human)


def apply_forward_triggers(response, agent):
    """Apply automatic forwarding based on response content."""
    forward_if_blank = agent.get("forward_if_blank")
    if forward_if_blank and (not response or response == f"{agent.name}:"):
        logger.info("Forward: blank, Using forward_if_blank")
        return f"@{forward_if_blank}"

    has_forward = chat.has_at_mention(response)

    forward_if_code = agent.get("forward_if_code")
    if not has_forward and forward_if_code and "```" in response:
        logger.info("Forward: code, Using forward_if_code")
        return f"@{forward_if_code}"

    forward_if_image = agent.get("forward_if_image")
    if not has_forward and forward_if_image and "![" in response:
        logger.info("Forward: image, Using forward_if_image")
        return f"@{forward_if_image}"

    return response


def determine_forward_target(response, agent, agents, config, room):
    """Determine which agent to forward to."""
    logger.info("Forward response: %r", response)
    response_message = list(bb_lib.lines_to_messages([response]))[-1]
    logger.info("response_message: %r", response_message)

    _responsible_human, bots2 = conductor.who_should_respond(
        response_message, agents=agents, history=[response_message], default=[],
        include_humans_for_ai_message=False, include_humans_for_human_message=False,
        may_use_mediator=False, config=config, room=room, include_self=False,
        at_only=True, use_aggregates=False,
    )

    bots2 = [b for b in bots2 if b is not None]

    if not bots2 and chat.has_at_mention(response):
        bots2 = [agent.get("forward_if_disallowed")]

    logger.info("Forward: who should respond: %r", bots2)
    return get_allowed_forward_target(bots2, agent)


def get_allowed_forward_target(bots2, agent):
    """Get the first allowed forward target from candidates."""
    forward_allow = agent.get("forward_allow")
    forward_deny = agent.get("forward_deny")

    for bot2 in reversed(bots2):
        if is_forward_denied(bot2, forward_allow, forward_deny):
            bot2 = agent.get("forward_if_denied")
            if not bot2:
                continue

        if bot2 == agent.name:
            logger.info("Skipping forwarding to self: %s", bot2)
            continue

        return bot2

    return None


def is_forward_denied(bot, forward_allow, forward_deny):
    """Check if forwarding to bot is denied."""
    if isinstance(forward_allow, list) and bot not in forward_allow:
        logger.info("Forward: %s not allowed, using forward_if_denied", bot)
        logger.info("  forward_allow: %r", forward_allow)
        return True

    if isinstance(forward_deny, list) and bot in forward_deny:
        logger.info("Forward: %s denied, using forward_if_denied", bot)
        logger.info("  forward_deny: %r", forward_deny)
        return True

    return False


async def execute_forward(bot2, agent, agents, file, args, history,
                        history_start, mission, summary, config, responsible_human):
    """Execute forwarding to another agent."""
    logger.info("Forwarding from %s to %s", agent.name, bot2)
    forward_keep_prompts = agent.get("forward_keep_prompts")
    agent2 = agents.get(bot2).apply_identity(agent, keep_prompts=forward_keep_prompts)
    # logger.info("Forward agent: %r", agent2)

    query = history[-1]
    response = await run_agent(
        agent2, query, file, args, history, history_start=history_start,
        mission=mission, summary=summary, config=config,
        agents=agents, responsible_human=responsible_human
    )

    if response is None:
        return None

    return response.lstrip().rstrip("\n ")


def apply_narrator_mode(response, agent):
    """Apply narrator mode transformations to response."""
    if agent.get("narrator") != "hard":
        return response

    response = response.lstrip(f'{agent.name}:')
    lines = response.split("\n")
    dedented = [line[1:] if line.startswith("\t") else line for line in lines]
    return "\n".join(dedented)


def should_poke_next(response, agent):
    """Determine if next agent should be poked based on response."""
    poke_if = agent.get("poke_if", [])
    poke = any(x in response for x in poke_if)
    # logger.info("poke_if: %r, poke: %r, response: %r", poke_if, poke, response)
    return poke


def update_skip_tracking(poke, skip, file):
    """Update skip tracking to avoid re-processing."""
    if not poke and skip is not None:
        logger.debug("Will skip processing after agent/s response: %r", file)
        skip[file] += 1


def filter_out_agents_install(response: str) -> str:
    """Install agents from a response by extracting YAML blocks and saving them to files."""
    # Extract YAML blocks
    logger.debug("filter_out_agents_install input response:\n\n%s", response)

    # remove indent and role label
    dedented_response = re.sub(r"^.*?\t", "", response, flags=re.MULTILINE)

    yaml_blocks = regex.findall(
        r"```yaml\n(.*?)```",
        dedented_response,
        flags=regex.DOTALL | regex.IGNORECASE
    )

    all_yaml = "".join(yaml_blocks)
    logger.debug("Found %d YAML blocks in response: %r", len(yaml_blocks), yaml_blocks)

    # Extract agent files
    yaml_agents = re.findall(
        r"^#File:\s*([^\n]+?\.yml)\s*?\n(.*?)(?=^#File:|\Z)",
        all_yaml,
        flags=regex.DOTALL | regex.MULTILINE | regex.IGNORECASE
    )

    logger.debug("Found %d agent files in YAML blocks: %r", len(yaml_agents), [name for name, _ in yaml_agents])

    agents_path = settings.PATH_ROOMS / "agents"

    for path_name, content in yaml_agents:
        # Sanitize filename

        # Process the path to remove components up to and including "agents" if present
        path_parts = Path(path_name).parts
        if "agents" in path_parts:
            agents_index = path_parts.index("agents")
            safe_path_name = Path(*path_parts[agents_index + 1:])
        else:
            # If "agents" not found, use the original path
            safe_path_name = Path(path_name)

        file_path = agents_path / safe_path_name

        # Validate path
        if not str(file_path).startswith(str(agents_path) + os.sep):
            logger.warning("Attempted to install agent outside agents folder: %s", file_path)
            continue

        try:
            # Create directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)

            util.backup_file(str(file_path))

            # Write content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content.strip() + "\n")
            logger.info("Successfully installed agent: %s", file_path)

        except (OSError, IOError) as e:
            logger.error("Failed to write agent file %s: %s", file_path, str(e))
            continue

    return response


def filter_in_think_add_example(response: str, place: int, example: str = "I was thinking... what was I thinking...?") -> str:
    """Add an example <think> section to the response, if not already present."""
    # TODO make sure it's own message, not another agent's message
    # TODO maybe not needed?
    if place == 1 and "<think>" not in response:
        response = re.sub("\t", f"\t<think>{example}</think>\n\t", response, count=1)
    return response


def filter_in_think_brackets(response: str, place: int) -> str:
    """Replace <think>thinking sections</think> with [thinking sections]"""
    response = re.sub(r"<think>(.*?)</think>", lambda thought: f"[{thought.group(1).strip()}]", response, flags=re.DOTALL)
    return response


def filter_out_think_brackets(response: str) -> str:
    """Replace [thinking sections] with <think>thinking sections</think>"""
    # match at start and end of lines only, so we don't match images / links
    response = re.sub(r"\t\[(.*?)\]$", r"\t<think>\1</think>", response, flags=re.DOTALL|re.MULTILINE)
    return response


def filter_out_actions_reduce(response: str, keep_prob: int = 0.5) -> str:
    """Reduce the number of *actions* in the response, based on keep_prob (0-1)."""
    response2 = re.sub(r" *\*(.*?) (.*?)\*[.!?]* *",
        lambda action: action.group(0) if random.random() < keep_prob else " ",
        response, flags=re.DOTALL)

    # strip leading/trailing spaces on each line
    response2 = re.sub(r"^\t +", "\t", response2, flags=re.MULTILINE)
    response2 = re.sub(r" +$", "", response2, flags=re.MULTILINE)

    # reduce multiple blank lines
    response2 = re.sub(r"\n{3,}", "\n\n", response2)
    if response2 and not re.search(r":\t?$", response2):
        return response2
    else:
        return response


def filter_out_emojis(response: str, keep_prob: float = 0.0) -> str:
    """Reduce the number of emojis in the response, based on keep_prob (0-1)."""
    # TODO implement probabilistic keeping of emojis
    if keep_prob == 0.0:
        return re.sub(r'[\U0001F300-\U0001F6FF]', '', response)
    if keep_prob == 1.0:
        return response
    return re.sub(r'[\U0001F300-\U0001F6FF]', lambda m: m.group(0) if random.random() < keep_prob else '', response)


def filter_out_emdash(response: str, keep_prob: float = 0.0, replacement: str = "-") -> str:
    """Replace em-dash characters with a replacement string, based on keep_prob (0-1)."""
    # Handle different types of em-dashes and their Unicode variants
    emdash_pattern = r'( *)(?:[-\u2014\u2013\u2015] *?)+( *)' # includes em-dash, en-dash, and horizontal bar

    if keep_prob == 0.0:
        return re.sub(emdash_pattern, "\1"+replacement+"\2", response)
    if keep_prob == 1.0:
        return response
    return re.sub(emdash_pattern, lambda m: m.group(0) if random.random() < keep_prob else m.group(1)+replacement+m.group(2), response)


filters_in = {
    "think_add_example": filter_in_think_add_example,
    "think_brackets": filter_in_think_brackets,
}


filters_out = {
    "agents_install": filter_out_agents_install,
    "think_brackets": filter_out_think_brackets,
    "actions_reduce": filter_out_actions_reduce,
    "emojis": filter_out_emojis,
    "emdash": filter_out_emdash,
}


def apply_filters_in(agent: ally_agents.Agent, query: str, history: list[str]) -> tuple[str, list[str]]:
    """Apply input filters to the query and history."""
    filters = agent.get("filter_in")
    history_new = None

    for filter_name in filters or []:
        if isinstance(filter_name, list):
            filter_args = filter_name[1:]
            filter_name = filter_name[0]
        else:
            filter_args = []
        filter_fn = filters_in.get(filter_name)
        if not filter_fn:
            logger.warning("Agent %r: Unknown filter_in: %r", agent.name, filter_name)
            continue
        if history_new is None:
            history_new = history.copy()
        try:
            query = filter_fn(query, 0, *filter_args)
            l = len(history_new)
            # NOTE: history[-1] is similar to query, but with the username prefix
            for i in range(l):
                history_new[i] = filter_fn(history_new[i], l - i, *filter_args)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Agent %r: Error in filter_in %r: %s", agent.name, filter_name, str(e))

    if history_new is not None:
        history = history_new

    return query, history


def apply_filters_out(agent: ally_agents.Agent, response: str) -> str:
    """Apply output filters to the response."""
    filters = agent.get("filter_out")
    for filter_name in filters or []:
        if isinstance(filter_name, list):
            filter_args = filter_name[1:]
            filter_name = filter_name[0]
        else:
            filter_args = []
        filter_fn = filters_out.get(filter_name)
        if not filter_fn:
            logger.warning("Agent %r: Unknown filter_out: %r", agent.name, filter_name)
            continue
        try:
            logger.debug("response before filter %r:\n%s", filter_name, response)
            response = filter_fn(response, *filter_args)
            logger.debug("response after filter %r:\n%s", filter_name, response)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Agent %r: Error in filter_out %r: %s", agent.name, filter_name, str(e))
    return response


async def run_agent(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None, responsible_human=None) -> str:
    """Run an agent."""
    limit_user = agent.get("limit_user")
    if limit_user and responsible_human not in limit_user:
        return None
    function = agent["fn"]
    logger.debug("query: %r", query)
    # TODO filter_in somehow. Perhaps distinct options to filter only the immediate input message, or the whole context.
    # TODO agent invocation options to limit context
    logger.debug("Applying input filters, query before: %r", query)
    query, history = apply_filters_in(agent, query, history)
    logger.debug("Applying input filters, query after: %r", query)

    response = await function(agent, query, file, args, history, history_start=history_start, mission=mission, summary=summary, config=config, agents=agents, responsible_human=responsible_human)

    logger.debug("Applying output filters, response before:\n%s", response)
    response = apply_filters_out(agent, response)
    logger.debug("Applying output filters, response after:\n%s", response)

    return response


async def run_subprocess(command, query):
    """Run a subprocess asynchronously."""
    # Create the subprocess
    proc = await asyncio.create_subprocess_exec(
        *command, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )

    # Write to stdin
    proc.stdin.write(query.encode("utf-8"))
    await proc.stdin.drain()
    proc.stdin.close()

    # Read stdout and stderr
    stdout, stderr = await proc.communicate()

    # Get the return code
    return_code = await proc.wait()

    return stdout.decode("utf-8"), stderr.decode("utf-8"), return_code


async def run_tool(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None, responsible_human: str=None) -> str:
    """Run a tool agent"""
    return await run_safe_shell(agent, query, file, args, history, history_start=history_start, mission=mission, summary=summary, config=config, agents=agents, responsible_human=responsible_human, direct=True)


async def run_safe_shell(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None, responsible_human: str=None, direct: bool=False) -> str:
    """Run a shell agent."""
    # NOTE: responsible_human is not used here

    name = agent.name
    logger.debug("history: %r", history)
    history_messages = list(bb_lib.lines_to_messages(history))
    logger.debug("history_messages: %r", history_messages)
    message = history_messages[-1]
    query = message["content"]

    try:
        executable = agent["command"][0]
    except (TypeError, KeyError):
        raise ValueError(f"Agent {name} has no command")

    query = chat.clean_prompt([query], name, args.delim) + "\n"
    logger.debug("query: %s", query)

    if direct:
        # tool must exist under PATH_TOOLS
        # check only contains safe characters
        if not re.match(r"^[a-zA-Z0-9._-]+$", executable):
            raise ValueError(f"Tool command contains unsafe characters: {executable}, {agent.name}")
        if not (settings.PATH_TOOLS/executable).is_file():
            # glob .* anywhere under it
            commands = list(settings.PATH_TOOLS.glob(f"**/{executable}.*"))
            if len(commands) == 0:
                raise ValueError(f"Tool command not found: {executable}, {agent.name}")
            if len(commands) > 1:
                raise ValueError(f"Tool command is ambiguous: {executable} matches {commands}, {agent.name}")
            executable = str(commands[0])

#    logger.debug("query 1: %r", query)
#    rx = r"((ok|okay|hey|hi|ho|yo|hello|hola)\s)*\b" + re.escape(name) + r"\b"
#    logger.debug("rx: %r", rx)
#    query = re.sub(rx, "", query, flags=re.IGNORECASE)
#    logger.debug("query 2: %r", query)
#    query = re.sub(r"^\s*[,;.]|\s*$", "", query).strip()
#    logger.debug("query 3: %r", query)

    args = []
    if agent.get("args"):
        args = query.split()
        query = ""

    if direct:
        command = [str(executable)] + agent["command"][1:] + args

        logger.debug("tool command: %r query: %r", command, query)
    else:
        argv = agent["command"] + args

        # shell escape in python
        cmd_str = ". ~/.profile ; "
        cmd_str += " ".join(map(shlex.quote, argv))

        command = ["sshc", "--", "nobodally@localhost", "bash", "-c", cmd_str]

        logger.debug("safe_shell command: %r query: %r", command, query)

    # echo the query to the subprocess
    output, errors, status = await run_subprocess(command, query)

    eol = not output or output.endswith("\n")
    if not eol:
        output += "\n"

    # format the response
    response = ""
    if errors or status:
        info = []
        if status:
            info.append(f"status: {status}")
        if info:
            response += ", ".join(info) + "\n\n"
        if errors:
            response += "## messages:\n```\n" + errors + "\n```\n\n"
        response += "## output:\n"

    response += format_tool_response(agent, output)

    response2 = f"{name}:\t{response}"
    logger.debug("response2:\n%r", response2)
    response3 = chat.fix_response_layout(response2, args, agent)
    logger.debug("response3:\n%s", response3)
    return response3


def python_tool_agent_yaml(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None, responsible_human: str=None, direct: bool=False) -> str:
    """Return a YAML definition for a python_tool agent, optionally filtered by grep pattern."""

    # Split remaining args as agent names
    args = query.split()
    grep_pattern = None

    # Extract grep pattern if present
    for i, arg in enumerate(args):
        if arg.startswith('-g='):
            grep_pattern = arg[3:]
            args.pop(i)
            break

    result = []
    for name in args:
        agent = agents.get(name)
        if agent:
            file_content = agent.get_file().rstrip()

            # Apply grep filter if pattern specified
            if grep_pattern:
                filtered_lines = []
                for line in file_content.split('\n'):
                    if re.search(grep_pattern, line):
                        filtered_lines.append(line)
                file_content = '\n'.join(filtered_lines)

            result.append(file_content)
        else:
            result.append(f"Agent '{name}' not found")

    return "\n\n".join(result)


python_tools = {
    "agent_yaml": python_tool_agent_yaml,
}


async def run_python(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None, responsible_human: str=None, direct: bool=False) -> str:
    """Run a python tool agent."""
    name = agent.name
    history_messages = list(bb_lib.lines_to_messages(history))
    message = history_messages[-1]
    query = message["content"]

    try:
        function_name = agent["command"][0]
    except (TypeError, KeyError):
        raise ValueError(f"Agent {name} has no command")
    if function_name not in python_tools:
        raise ValueError(f"Python function not found: {function_name}")
    function = python_tools[function_name]

    query = chat.clean_prompt([query], name, args.delim) + "\n"

    # Prepare response formatting
    response = ""
    try:
        result = function(agent, query, file, args, history, history_start, mission, summary, config, agents, responsible_human, direct)

        # Handle the output
        if isinstance(result, str):
            output = result
        else:
            output = repr(result)

        # Add newline if missing
        if not output.endswith('\n'):
            output += '\n'

    except Exception as e:
        error_msg = f"Error executing {function_name}: {str(e)}"
        response += f"status: error\n\n## messages:\n```\n{error_msg}\n```\n\n## output:\n"
        output = "Function execution failed"

    # Format the output according to agent's format specification
    response += format_tool_response(agent, output)

    response2 = f"{name}:\t{response}"
    response3 = chat.fix_response_layout(response2, args, agent)
    return response3


def format_tool_response(agent, output):
    """Format the tool response based on agent settings."""
    fmt = agent.get("format", "code")
    if fmt == "code":
        return "```\n" + output + "```\n"
    elif fmt in ["markdown", "html"]:
        return output
    elif fmt == "pre":
        return "<pre>\n" + output + "</pre>\n"
    else:
        raise ValueError(f"Unknown format: {fmt}")


async def file_changed(file_path, change_type, old_size, new_size, args, skip, agents):
    """Process a file change."""
    logger.info("change, old_size, new_size: %r, %r, %r", change_type, old_size, new_size)

    if args.ext and not file_path.endswith(args.ext):
        return
    if change_type == Change.deleted:
        return
    if not args.shrink and old_size and new_size < old_size:
        return
    if old_size is None:
        return
    if new_size == 0 and old_size != 0:
        return

    poke = new_size == old_size

    if skip.get(file_path):
        logger.debug("Won't react to AI response: %r", file_path)
        skip[file_path] -= 1
        return

    try:
        logger.debug("Processing file: %r", file_path)
        count = await process_file(file_path, args, skip=skip, agents=agents, poke=poke)
        logger.debug("Processed file: %r, %r agents responded", file_path, count)
    except Exception:  # pylint: disable=broad-except
        logger.exception("Processing file failed: %r", file_path, exc_info=True)


def check_file_type(path):
    """Check the file type, either room or agent."""
    ext = Path(path).suffix
    if ext == ".bb" and path.startswith(str(settings.PATH_ROOMS)+"/"):
        return "room"
    if ext == ".yml" and path.startswith(str(settings.PATH_AGENTS)+"/"):
        return "agent"
    if ext == ".yml" and path.startswith(str(settings.PATH_ROOMS/"agents")+"/"):
        return "agent"
    if ext == ".yml" and path.startswith(str(settings.PATH_ROOMS)+"/") and "agents" in Path(path).parts and not Path(path).is_symlink():
        return "agent_private"
    if ext in [".safetensors"] and path.startswith(str(settings.PATH_ROOMS)+"/"):
        return "contrib"
    return None


def move_contrib(path: Path) -> None:
    """Move contributed files to the main contrib folder"""
    dest = str(settings.PATH_ROOMS) + "/contrib"
    if str(path).startswith(dest + "/"):
        return
    Path(dest).mkdir(parents=True, exist_ok=True)
    logger.info("Moving %s to %s", path, dest)
    Path(path).rename(Path(dest) / Path(path).name)


async def watch_loop(args):
    """Follow the watch log, and process files."""
    skip = defaultdict(int)

    agents = ally_agents.Agents(services)
    agents.load(settings.PATH_AGENTS)
    rooms_public_agents = settings.PATH_ROOMS/"agents"
    agents.load(rooms_public_agents)

    for agents_dir in Path(settings.PATH_ROOMS).rglob('agents'):
        if agents_dir == rooms_public_agents:
            continue
        if agents_dir.is_dir():
            agents.load(agents_dir, private=True)

    agents.write_agents_list(settings.PATH_ROOMS / ".agents_global.yml")

    async with atail.AsyncTail(filename=args.watch, follow=True, rewind=True) as queue:
        while (line := await queue.get()) is not None:
            try:
                file_path, change_type, old_size, new_size = line.rstrip("\n").split("\t")
                change_type = Change(int(change_type))
                old_size = int(old_size) if old_size != "" else None
                new_size = int(new_size) if new_size != "" else None

                file_type = check_file_type(file_path)

                logger.info("File change detected: %r, type: %r", file_path, file_type)

                if file_type == "room" and not os.access(file_path, os.W_OK):
                    logger.info("Ignoring change to unwritable file: %r", file_path)
                elif file_type == "room":
                    task = asyncio.create_task(file_changed(file_path, change_type, old_size, new_size, args, skip, agents))
                    tasks.add_task(task, f"file changed: {file_path}")
                    tasks.list_active_tasks()
                elif file_type == "agent":
                    agents.handle_file_change(file_path, change_type)
                    agents.write_agents_list(settings.PATH_ROOMS / ".agents_global.yml")
                elif file_type == "agent_private":
                    agents.handle_file_change(file_path, change_type, private=True)
                elif file_type == "contrib" and change_type == Change.added:
                    move_contrib(file_path)
                else:
                    logger.debug("Ignoring change to file: %r", file_path)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Error processing file change", exc_info=True)
            finally:
                queue.task_done()


async def restart_service():
    """Restart the service."""
    await tasks.wait_for_tasks()
    command_line = [sys.executable] + sys.argv
    logger.debug("Restarting service: %r", command_line)
    logger.info("Restarting service")
    sys.stderr.write("\n")
    os.execv(sys.executable, command_line)


def get_code_files():
    code_files = [os.path.realpath(__file__)]

    # all module source files
    # TODO this is incomplete, it doesn't catch all modules
    for mod in sys.modules.values():
        file = getattr(mod, "__file__", None)
        if file and file.startswith(str(settings.PATH_HOME)) and not "/venv/" in file and file.endswith(".py"):
            code_files.append(mod.__file__)

    return code_files


async def reload_module(module_name: str, module, file_stem: str) -> tuple[bool, str | None]:
    """
    Attempt to reload a single module.
    Returns (success, error_message)
    """
    if module is None:
        return False, None

    # Check if module name matches the file stem
    if not (module_name == file_stem or module_name.endswith(f".{file_stem}")):
        return False, None

    try:
        reloaded_module = importlib.reload(module)
        # Update sys.modules with the reloaded module
        sys.modules[module_name] = reloaded_module
        # Update the global namespace
        globals()[module_name.split('.')[-1]] = reloaded_module
        return True, None
    except ImportError as e:
        return False, str(e)


async def process_changed_code_file(file: str) -> tuple[set[str], list[str]]:
    """
    Process a single changed file and attempt to reload corresponding module.
    Returns (reloaded_modules, need_restart_files)
    """
    reloaded = set()
    need_restart_files = []

    file_stem = Path(file).stem

    # Check if this file corresponds to a reloadable module
    if file_stem not in RELOADABLE_MODULES:
        need_restart_files.append(file)
        return reloaded, need_restart_files

    # Try to reload matching modules
    for module_name, module in list(sys.modules.items()):
        success, error = await reload_module(module_name, module, file_stem)
        if success:
            reloaded.add(module_name)
            break
        elif error:
            logger.error("Failed to reload module %s: %s", module_name, error)
            need_restart_files.append(file)
            break
    else:
        need_restart_files.append(file)

    return reloaded, need_restart_files


async def reload_if_code_changes():
    """Watch for code changes and reload affected modules."""
    code_files = get_code_files()
    logger.debug("watching code files: %r", code_files)

    async for changes in awatch(*code_files, debounce=1000, debug=False):
        all_reloaded = set()
        all_need_restart = []

        for _change, file in changes:
            logger.info("Code file changed: %r", file)
            reloaded, need_restart = await process_changed_code_file(file)
            all_reloaded.update(reloaded)
            all_need_restart.extend(need_restart)

        if all_reloaded:
            logger.info("Reloaded modules: %s", ", ".join(sorted(all_reloaded)))
            setup_services()

        if all_need_restart:
            logger.info("Need restart for:")
            for file in all_need_restart:
                logger.info("- %s", file)
            await restart_service()


async def restart_if_code_changes():
    """Watch for code changes and restart the service. Not used now."""
    code_files = get_code_files()
    logger.debug("watching code files: %r", code_files)

    try:
        async for changes in awatch(*code_files, debounce=1000, debug=False):
            for _change, file in changes:
                logger.info("Code file changed: %r", file)
            await restart_service()
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("Error watching code files", exc_info=e)
        await restart_service()


services: dict[str, dict[str, Any]] = {}


def setup_services():
    global services
    services = {
        "llm_llama":    {"link": "portal", "fn": local_agents.local_agent},
        "image_a1111":  {"link": "portal", "fn": local_agents.local_agent, "dumb": True},
        "image_openai": {"link": "remote", "fn": remote_agents.remote_agent, "dumb": True},  # TODO
        "openai":       {"link": "remote", "fn": remote_agents.remote_agent},
        "anthropic":    {"link": "remote", "fn": remote_agents.remote_agent},
        "google":       {"link": "remote", "fn": remote_agents.remote_agent},
        "perplexity":   {"link": "remote", "fn": remote_agents.remote_agent},
        "xai":          {"link": "remote", "fn": remote_agents.remote_agent},
        "deepseek":     {"link": "remote", "fn": remote_agents.remote_agent},
        "openrouter":   {"link": "remote", "fn": remote_agents.remote_agent},
        "venice":       {"link": "remote", "fn": remote_agents.remote_agent},
        "safe_shell":   {"link": "tool", "fn": run_safe_shell, "safe": False, "dumb": True},  # ironically
        "tool":         {"link": "tool", "fn": run_tool, "dumb": True},
        "search":       {"link": "tool", "fn": run_search, "dumb": True},
        "python":       {"link": "tool", "fn": run_python, "dumb": True},
    }


def get_opts():  # pylint: disable=too-many-statements
    """Get the command line options."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    modes_group = parser.add_argument_group("Modes of operation")
    modes_group.add_argument("--watch", "-w", default=None, help="Watch mode, follow a watch log file")

    watch_group = parser.add_argument_group("Watch mode options")
    watch_group.add_argument("--ext", default=settings.EXTENSION, help="File extension to watch for")
    watch_group.add_argument("--shrink", action="store_true", help="React if the file shrinks")

    format_group = parser.add_argument_group("Format options")
    format_group.add_argument("--delim", default="\n\n", help="Delimiter between messages")
    format_group.add_argument(
        "--memory",
        "-x",
        type=int,
        default=32 * 1024 - 2048,
        help="Max number of tokens to keep in history, before we drop old messages",
    )

    model_group = parser.add_argument_group("Model options")
    model_group.add_argument("--model", "-m", default="default", help="Model name or path")
    model_group.add_argument("--config", "-c", default=None, help="Model config file, in YAML format")

    ucm.add_logging_options(parser)

    args = parser.parse_args()

    ucm.setup_logging(args)

    logger.debug("Options: %r", args)

    return args


async def main():
    """Main function."""
    args = get_opts()

    if not args.watch:
        raise ValueError("Watch file not specified")

    setup_services()

    local_agents.init(args)

    logger.info("Watching chat rooms")
    asyncio.create_task(reload_if_code_changes())
    await watch_loop(args)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("interrupted")
        sys.exit(0)
