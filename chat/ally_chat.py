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
from ally_room import Room
import fetch
import llm  # type: ignore
from ally.cache import cache  # type: ignore
import aligno_py as aligno  # type: ignore
from agents import Agents, Agent
from remote_agents import remote_agent
from local_agents import local_agent
import local_agents
from settings import *
import tasks
from ally import stopwords


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
    logger.debug("query 1: %r", query)
    # query = query.split("\n")[0]
    # logger.debug("query 2: %r", query)
    # rx = r'((ok|okay|hey|hi|ho|yo|hello|hola)\s)*\b'+re.escape(name)+r'\b'
    rx = r".*?\b" + re.escape(name) + r"\b"
    logger.debug("rx: %r", rx)
    query = re.sub(rx, "", query, flags=re.IGNORECASE | re.DOTALL)
    logger.debug("query 3: %r", query)
    query = re.sub(r"(show me|search( for|up)?|find( me)?|look( for| up)?|what(\'s| is) (the|a|an)?)\s+", "", query, flags=re.IGNORECASE)
    logger.debug("query 4: %r", query)
    query = re.sub(r"#.*", "", query)
    logger.debug("query 5: %r", query)
    query = re.sub(r"[^\x00-~]", "", query)  # filter out emojis
    logger.debug("query 6: %r", query)
    query = re.sub(r"^\s*[,;.]|[,;.]\s*$", "", query).strip()

    logger.debug("query: %r %r", engine_id, query)

    try:
        response = await search.search(query, engine=engine_id, markdown=True, num=num, limit=limit, safe=not ADULT)
    except requests.exceptions.HTTPError:
        if name != "Pr0nto":
            raise
        query2 = stopwords.strip_stopwords(query, strict=True)
        logger.info("Stripped stopwords from query: %r -> %r", query, query2)
        response = await search.search(query2, engine=engine_id, markdown=True, num=num, limit=limit, safe=not ADULT)

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
    top_dir = PATH_ROOMS
    if top_dir != room_dir and top_dir not in room_dir.parents:
        raise ValueError(f"Room directory {room_dir} is not under {top_dir}")

    agents_dirs = []

    while True:
        agents_dir = room_dir / "agents"
        if agents_dir.exists():
            agents_dirs.append(agents_dir)
        if room_dir == top_dir:
            break
        room_dir = room_dir.parent

    for agent_dir in reversed(agents_dirs):
        agents = Agents(services, parent=agents)
        agents.load(agent_dir, visual=False)

        agents.write_agents_list(agent_dir.parent / ".agents.yml")

        logger.info("Loaded agents from %s", agent_dir)
        logger.debug("Agents: %r", agents.names())

    return agents


async def process_file(file, args, history_start=0, skip=None, agents=None, poke=False) -> int:
    """Process a file, return True if appended new content."""
    logger.info("Processing %s", file)

    room = Room(path=Path(file))

    history = chat.chat_read(file, args)

    # Load config file, if present
    config_file = room.find_resource_file("yml", "options")
    logger.info("config_file: %r", config_file)
    config = config_read(config_file)
    logger.info("config: %r", config)

    mission_file_name = config.get("mission", "mission")
    mission_try_room_name = "mission" not in config

    # Load mission file, if present
    mission_file = room.find_resource_file("m", mission_file_name, try_room_name=mission_try_room_name)
    mission = chat.chat_read(mission_file, args)

    # logger.info("mission name %r, mission_try_room_name %r, mission_file %r", mission_file_name, mission_try_room_name, mission_file)

    # Load summary file, if present
    summary_file = room.find_resource_file("s", "summary")
    summary = summary_read(summary_file, args)

    # Load local agents
    agents = load_local_agents(room, agents)

    history_messages = list(bb_lib.lines_to_messages(history))

    message = history_messages[-1] if history_messages else None

    # check for editing commands, AI should not respond to these
    if message and not poke and re.search(r"""<ac\b[a-z0-9 ="']*>\s*$""", message["content"], flags=re.IGNORECASE):
        return 0

    # logger.info("history_messages 1: %r", history_messages)

    # flatten history, removing any editing commands
    history_messages = chat.apply_editing_commands(history_messages)

    message = history_messages[-1] if history_messages else None

    # so inefficient, need to rework this sensibly one day using ChatMessage objects
    history = list(bb_lib.messages_to_lines(history_messages))

#     logger.info("history_messages 2: %r", history_messages)
    # logger.info("history 2: %r", history)

    welcome_agents = [name for name, agent in agents.items() if agent.get("welcome")]

    include_self = config.get("self_talk", True) and not poke

    responsible_human, bots = conductor.who_should_respond(
        message,
        agents=agents,
        history=history_messages,
        default=welcome_agents,
        include_humans_for_ai_message=not poke,
        include_humans_for_human_message=not poke,  # True,
        mission=mission,
        config=config,
        room=room,
        include_self=include_self,
    )
    logger.info("who should respond: %r; responsible: %r", bots, responsible_human)

    # Support "directed-poke" which removes itself, like -@Ally
    # TODO this is a bit dodgy and has a race condition
    if message and message["content"].startswith("-@"):  # pylint: disable=unsubscriptable-object
        history_messages.pop()
        history.pop()
        room.undo("root")
        message = history_messages[-1] if history_messages else None

    count = 0
    for bot in bots:
        if not (bot and bot in agents.names()):
            continue

        agent = agents.get(bot)

        if agent.get("type") in [None, "human", "visual"]:
            continue

        poke_if = agent.get("poke_if", [])

        # load agent's mission file, if present
        my_mission = mission.copy()
        agent_mission_file = room.find_agent_resource_file("m", bot)
        mission2 = chat.chat_read(agent_mission_file, args)
        logger.debug("mission: %r", mission)
        logger.debug("mission2: %r", mission2)
        if mission2:
            my_mission += [""] + mission2

        #     - query is not even used in remote_agent
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
        logger.debug("history 1: %r", history)
        response = await run_agent(
            agent, query, file, args, history, history_start=history_start, mission=my_mission, summary=summary, config=config, agents=agents, responsible_human=responsible_human
        )
        response = response.lstrip().rstrip("\n ")

        # Forwarding to other agents transparently:
        # TODO use a function or something
        forward = agent.get("forward")
        forward_allow = agent.get("forward_allow")
        forward_deny = agent.get("forward_deny")
        forward_if_denied = agent.get("forward_if_denied")
        forward_if_code = agent.get("forward_if_code")
        forward_if_image = agent.get("forward_if_image")
        forward_if_blank = agent.get("forward_if_blank")
        forward_if_disallowed = agent.get("forward_if_disallowed")
        forward_keep_prompts = agent.get("forward_keep_prompts")

        if forward_if_blank and (not response or response == f"{agent.name}:"):
            logger.info("Forward: blank, Using forward_if_blank")
            response = f"@{forward_if_blank}"

        has_forward = chat.has_at_mention(response)

        # HACK: if the agent tried to give an image prompt or an image, forward it
        if not has_forward and forward_if_code and "```" in response:
            logger.info("Forward: code, Using forward_if_code")
            response = f"@{forward_if_code}"
        if not has_forward and forward_if_image and "![" in response:
            logger.info("Forward: image, Using forward_if_image")
            response = f"@{forward_if_image}"

        if forward and response:
            logger.info("Forward response: %r", response)
            # look for the final line @agent_name
            response_message = list(bb_lib.lines_to_messages([response]))[-1]
            _responsible_human, bots2 = conductor.who_should_respond(
                response_message,
                agents=agents,
                history=[response_message],
                default=[],
                include_humans_for_ai_message=False,
                include_humans_for_human_message=False,
                may_use_mediator=False,
                config=config,
                room=room,
                include_self=False,
                at_only=True,
                use_aggregates=False,
            )

            # HACK: if the agent tried to foward to an agent that is not allowed here, replace it
            if not bots2 and chat.has_at_mention(response):
                bots2 = [forward_if_disallowed]

            logger.info("Forward: who should respond: %r", bots2)
            for bot2 in bots2:
                if isinstance(forward_allow, list) and bot2 not in forward_allow or isinstance(forward_deny, list) and bot2 in forward_deny:
                    logger.info("Forward: %s not allowed, using forward_if_denied", bot2)
                    logger.info("  forward_allow: %r", forward_allow)
                    logger.info("  forward_deny: %r", forward_deny)
                    bot2 = agent.get("forward_if_denied")
                    if not bot2:
                        continue
                # never forward to self
                if bot2 == agent.name:
                    logger.info("Skipping forwarding to self: %s", bot2)
                    continue
                logger.info("Forwarding to %s", bot2)
                agent2 = agents.get(bot2).apply_identity(agent, keep_prompts=forward_keep_prompts)
                poke_if = agent2.get("poke_if", [])
                # replace agent.name with agent2.name in user's message
                # logger.info("Replacing %s with %s in query: %r", agent.name, agent2.name, query)
                # query2 = history[-1] = re.sub(rf"\b{re.escape(agent.name)}\b", agent2.name, query)
                # logger.info("  query2: %r", query2)
                response = await run_agent(
                    agent2, query, file, args, history, history_start=history_start, mission=my_mission, summary=summary, config=config, agents=agents, responsible_human=responsible_human
#                    agent2, query2, file, args, history, history_start=history_start, mission=my_mission, summary=summary, config=config, agents=agents, responsible_human=responsible_human
                )
                response = response.lstrip().rstrip("\n ")
                # if agent.get("forward") == "transparent_half" and response:
                #     response = f"{agent.name}:\t" + re.sub(r"\A.*?:(\t|$)", "", response, count=1, flags=re.MULTILINE)
                # elif agent.get("forward") == "transparent" and response:
                #     response = re.sub(rf"\b{re.escape(agent2.name)}\b", agent.name, response)
                break  # only forward to at most one agent, for now

        # Narrator agents:
        if agent.get("narrator") == "hard":
            response = response.lstrip(f'{agent.name}:')
            # remove 1 tab from start of each line
            response = "\n".join([line[1:] if line.startswith("\t") else line for line in response.split("\n")])

        # Anti Em-dash!  Could do this more generically for other substitutions
        if agent.get("anti_em"):
            response = re.sub(r"—", " - ", response)

        # Ephemeral messages:
        # If the previous message begins with - it was ephemeral, so remove it
        # TODO this might not work well when multiple bots respond
        if history and history[-1].startswith("-"):
            history.pop()
            history_messages.pop()
            room.undo("root")
            # sleep for a bit
            await asyncio.sleep(0.1)

        if response == f"{agent.name}:":
            response += ""

        poke = any(x in response for x in poke_if)
        logger.debug("poke_if: %r, poke: %r, response: %r", poke_if, poke, response)

        history.append(response)
        logger.debug("history 2: %r", history)
        # avoid re-processing in response to an AI response
        if not poke and skip is not None:
            logger.debug("Will skip processing after agent/s response: %r", file)
            skip[file] += 1
        chat.chat_write(file, history[-1:], delim=args.delim, invitation=args.delim)

        count += 1
    return count


async def run_agent(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None, responsible_human=None) -> str:
    """Run an agent."""
    function = agent["fn"]
    logger.debug("query: %r", query)
    return await function(agent, query, file, args, history, history_start=history_start, mission=mission, summary=summary, config=config, agents=agents, responsible_human=responsible_human)


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


async def safe_shell(agent, query, file, args, history, history_start=0, command=None, mission=None, summary=None, config=None, agents=None, responsible_human: str=None):
    """Run a shell agent."""
    # NOTE: responsible_human is not used here

    name = agent.name
    logger.debug("history: %r", history)
    history_messages = list(bb_lib.lines_to_messages(history))
    logger.debug("history_messages: %r", history_messages)
    message = history_messages[-1]
    query = message["content"]

#    logger.debug("query 1: %r", query)
#    rx = r"((ok|okay|hey|hi|ho|yo|hello|hola)\s)*\b" + re.escape(name) + r"\b"
#    logger.debug("rx: %r", rx)
#    query = re.sub(rx, "", query, flags=re.IGNORECASE)
#    logger.debug("query 2: %r", query)
#    query = re.sub(r"^\s*[,;.]|\s*$", "", query).strip()
#    logger.debug("query 3: %r", query)

    query = chat.clean_prompt([query], name, args.delim)
    logger.debug("query: %s", query)

    # shell escape in python
    cmd_str = ". ~/.profile ; "
    cmd_str += " ".join(map(shlex.quote, agent["command"]))

    command = ["sshc", "--", "allemande-nobody@localhost", "bash", "-c", cmd_str]

    # echo the query to the subprocess
    output, errors, status = await run_subprocess(command, query)

    eol = not output or output.endswith("\n")
    if not eol:
        output += "\n"

    # format the response
    response = ""
    if errors or status or not eol:
        info = []
        if status:
            info.append(f"status: {status}")
        if not eol:
            info.append("no EOL")
        if info:
            response += ", ".join(info) + "\n\n"
        if errors:
            response += "## errors:\n```\n" + errors + "\n```\n\n"
        response += "## output:\n"
    response += "```\n" + output + "```\n"

    response2 = f"{name}:\t{response}"
    response3 = chat.fix_response_layout(response2, args, agent)
    logger.debug("response3:\n%s", response3)
    return response3


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
        logger.exception("Processing file failed", exc_info=True)


def check_file_type(path):
    """Check the file type, either room or agent."""
    ext = Path(path).suffix
    if ext == ".bb" and path.startswith(str(PATH_ROOMS)+"/"):
        return "room"
    if ext == ".yml" and path.startswith(str(PATH_AGENTS)+"/"):
        return "agent"
    if ext == ".yml" and path.startswith(str(PATH_ROOMS)+"/") and Path(path).parent.name == "agents" and not Path(path).is_symlink():
        return "agent_private"
    if ext in [".safetensors"] and path.startswith(str(PATH_ROOMS)+"/"):
        return "contrib"
    return None


def move_contrib(path: Path) -> None:
    """Move contributed files to the main contrib folder"""
    dest = str(PATH_ROOMS) + "/contrib"
    if str(path).startswith(dest + "/"):
        return
    Path(dest).mkdir(parents=True, exist_ok=True)
    logger.info("Moving %s to %s", path, dest)
    Path(path).rename(Path(dest) / Path(path).name)


async def watch_loop(args):
    """Follow the watch log, and process files."""
    skip = defaultdict(int)

    agents = Agents(services)
    agents.load(PATH_AGENTS)

    for agents_dir in Path(PATH_ROOMS).rglob('agents'):
        if agents_dir.is_dir():
            agents.load(agents_dir, private=True)

    agents.write_agents_list(PATH_ROOMS / ".agents_global.yml")

    async with atail.AsyncTail(filename=args.watch, follow=True, rewind=True) as queue:
        while (line := await queue.get()) is not None:
            try:
                file_path, change_type, old_size, new_size = line.rstrip("\n").split("\t")
                change_type = Change(int(change_type))
                old_size = int(old_size) if old_size != "" else None
                new_size = int(new_size) if new_size != "" else None

                file_type = check_file_type(file_path)

                if file_type == "room" and not os.access(file_path, os.W_OK):
                    logger.info("Ignoring change to unwritable file: %r", file_path)
                elif file_type == "room":
                    task = asyncio.create_task(file_changed(file_path, change_type, old_size, new_size, args, skip, agents))
                    tasks.add_task(task, f"file changed: {file_path}")
                    tasks.list_active_tasks()
                elif file_type == "agent":
                    agents.handle_file_change(file_path, change_type)
                    agents.write_agents_list(PATH_ROOMS / ".agents_global.yml")
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
        if file and file.startswith(str(PATH_HOME)) and not "/venv/" in file and file.endswith(".py"):
            code_files.append(mod.__file__)

    return code_files


async def restart_if_code_changes():
    """Watch for code changes and restart the service."""
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


services = {
    "llm_llama":    {"link": "portal", "fn": local_agent},
    "image_a1111":  {"link": "portal", "fn": local_agent, "dumb": True},
    "image_openai": {"link": "remote", "fn": remote_agent, "dumb": True},  # TODO
    "openai":       {"link": "remote", "fn": remote_agent},
    "anthropic":    {"link": "remote", "fn": remote_agent},
    "google":       {"link": "remote", "fn": remote_agent},
    "perplexity":   {"link": "remote", "fn": remote_agent},
    "xai":          {"link": "remote", "fn": remote_agent},
    "deepseek":     {"link": "remote", "fn": remote_agent},
    "openrouter":   {"link": "remote", "fn": remote_agent},
    "venice":       {"link": "remote", "fn": remote_agent},
    "safe_shell":   {"link": "tool", "fn": safe_shell, "safe": False, "dumb": True},  # ironically
    "search":       {"link": "tool", "fn": run_search, "dumb": True},
}


def get_opts():  # pylint: disable=too-many-statements
    """Get the command line options."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    modes_group = parser.add_argument_group("Modes of operation")
    modes_group.add_argument("--watch", "-w", default=None, help="Watch mode, follow a watch log file")

    watch_group = parser.add_argument_group("Watch mode options")
    watch_group.add_argument("--ext", default=EXTENSION, help="File extension to watch for")
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

    local_agents.init(args)

    logger.info("Watching chat rooms")
    asyncio.create_task(restart_if_code_changes())
    await watch_loop(args)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("interrupted")
        sys.exit(0)
