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
from ally import portals  # type: ignore
from ally.cache import cache  # type: ignore
import aligno_py as aligno  # type: ignore
from ally import re_map
from agents import Agents, Agent

Message = dict[str, Any]

os.environ["TRANSFORMERS_OFFLINE"] = "1"
import transformers  # type: ignore # pylint: disable=wrong-import-position, wrong-import-order

PATH_HOME   = Path(os.environ["ALLEMANDE_HOME"])
PATH_ROOMS  = Path(os.environ["ALLEMANDE_ROOMS"])
PATH_AGENTS = Path(os.environ["ALLEMANDE_AGENTS"])
PATH_VISUAL = Path(os.environ["ALLEMANDE_VISUAL"])
PATH_MODELS = Path(os.environ["ALLEMANDE_MODELS"])
PATH_WEBCACHE  = Path(os.environ["ALLEMANDE_WEBCACHE"])
# TODO put agents dir in rooms?

# TODO put some of these settings in a global reloadable config files
STARTER_PROMPT = """System:\tPlease briefly greet the user or start a conversation, in one line. You can creative, or vanilla."""

logger = logging.getLogger(__name__)
logging.getLogger('watchfiles').setLevel(logging.WARNING)

LOCAL_AGENT_TIMEOUT = 5 * 60  # 5 minutes
FETCH_TIMEOUT = 30  # 30 seconds

DEFAULT_FILE_EXTENSION = "bb"

REMOTE_AGENT_RETRIES = 3

MAX_REPLIES = 1

ADULT = os.environ.get("ALLYCHAT_ADULT", "0") == "1"
SAFE = os.environ.get("ALLYCHAT_SAFE", "1") == "1"

TOKENIZERS: dict[str, transformers.AutoTokenizer] = {}

Messasge = dict[str, Any]


def load_tokenizer(model_path: Path):
    """Load the Llama tokenizer"""
    return transformers.AutoTokenizer.from_pretrained(str(model_path))


def count_tokens_in_text(text, tokenizer):
    """Count the number of tokens in a text."""
    return len(tokenizer(text).input_ids)


def trim_response(response, args, agent_name, people_lc=None):
    """Trim the response to the first message."""
    if people_lc is None:
        people_lc = []

    def check_person_remove(match):
        """Remove text starting with a known person's name."""
        if match.group(2).lower() in people_lc:
            return ""
        return match.group(1)

    response = response.strip()

    response_before = response

    # remove agent's own `name: ` from response
    agent_name_esc = re.escape(agent_name)
    response = re.sub(r"^[ \t]*" + agent_name_esc + r"[ \t]*:[ \t]*(.*)", r"\1", response, flags=re.MULTILINE)

    # remove anything after a known person's name
    response = re.sub(r"(\n[ \t]*(\w+)[ \t]*:[ \t]*(.*))", check_person_remove, response, flags=re.DOTALL)

    # response = re.sub(r"\n(##|<nooutput>|<noinput>|#GPTModelOutput|#End of output|\*/\n\n// End of dialogue //|// end of output //|### Output:|\\iend{code})(\n.*|$)", "", response , flags=re.DOTALL|re.IGNORECASE)

    if response != response_before:
        logger.debug("Trimmed response: %r\nto: %r", response_before, response)

    response = " " + response.strip()
    return response


def leading_spaces(text):
    """Return the number of leading spaces in a text."""
    return re.match(r"\s*", text).group(0)


def fix_layout(response, _args, agent):
    """Fix the layout and indentation of the response."""
    logger.debug("response before fix_layout: %s", response)
    lines = response.strip().split("\n")
    out = []
    in_table = False
    in_code = False

    if agent.get("strip_triple_backticks"):
        if lines and "```" in lines[0]:
            lines[0] = re.sub(r"```\w*\s*", "", lines[0])
            if lines[0].endswith("\t"):
                lines[1] = lines[0] + lines[1].strip()
                lines.pop(0)
        lines = [line for line in lines if not re.match(r"\t?```\w*\s*$", line)]

    # Remove agent's name, if present
    logger.debug("lines[0]: %r", lines[0])
    logger.debug("agent.name: %r", agent.name)
    name_part = None
    if lines[0].startswith(agent.name + ":\t"):
        name_part, lines[0] = lines[0].split(":\t", 1)
    logger.debug("lines[0] after: %r", lines[0])
    logger.debug("name_part: %r", name_part)

    # First line may be indented differently
    lines[0] = lines[0].strip()

    # detect common indent
    common_indent = aligno.find_common_indent(lines[1:])

    # clean up the lines
    for i, line in enumerate(lines):
        # strip common indent
        if line.startswith(common_indent):
            line = line[len(common_indent) :]

        line = line.rstrip()

        # markdown tables must have a blank line before them ...
        if not in_table and ("---" in line or re.search(r"\|.*\|", line)):
            if i > 0 and lines[i - 1].strip():
                out.append("")
            in_table = True

        if in_table and not line.strip():
            in_table = False

#         # detect if in_code
#         if not in_code and (re.search(r"```", line) or re.search(r"<script\b", line)):
#             in_code = True
#             line1 = line
#             if i == 0:
#                 line1 = re.sub(r"^[^\t]*", "", line1)
#             base_indent = leading_spaces(line1)
#         elif in_code and (re.search(r"```", line) or re.search(r"</script>", line)):
#             in_code = False
#
#         if in_code:
#             # For code, try to remove base_indent from the start of the line
#             if base_indent and line.startswith(base_indent):
#                 line = line[len(base_indent) :]
#             else:
#                 base_indent = ""
#             if i > 0:
#                 line = "\t" + line
#         else:
# #            # For non-code, strip all leading tabs and trailing whitespace, to avoid issues
# #            line = line.lstrip("\t").rstrip()
#             line = line.rstrip()
#             if i > 0:
#                 line = "\t" + line
#             elif "\t" not in line:
#                 line = line + "\t"

        if i == 0 and name_part:
            line = name_part + ":\t" + line
        else:
            line = "\t" + line
        out.append(line)

    response = ("\n".join(out)).rstrip()

    logger.debug("response after fix_layout: %s", response)

    return response


def get_fulltext(args, model_name, history, history_start, invitation, delim):
    """Get the full text from the history, and cut to the right length."""
    # FIXME this sync function is potentially slow
    tokenizer = TOKENIZERS[model_name]
    fulltext = delim.join(history[history_start:]) + invitation
    n_tokens = count_tokens_in_text(fulltext, tokenizer)
    logger.debug("n_tokens is %r", n_tokens)
    # dropped = False
    # TODO use a better search method
    last = False
    while n_tokens > args.memory:
        if len(history) - history_start < 10:
            guess = 1
        else:
            logger.debug("guessing how many tokens to drop...")
            logger.debug("  args.memory: %r", args.memory)
            logger.debug("  n_tokens: %r", n_tokens)
            logger.debug("  len(history): %r", len(history))
            logger.debug("  history_start: %r", history_start)
            guess = ((n_tokens - args.memory) / n_tokens) * (len(history) - history_start)
            guess = int(guess * 0.7)
            logger.debug("  guess: %r", guess)
            if guess <= 0:
                guess = 1
            if guess >= len(history) - history_start:
                guess = len(history) - history_start - 1
                last = 1
        history_start += guess
        fulltext = delim.join(history[history_start:]) + invitation
        n_tokens = count_tokens_in_text(fulltext, tokenizer)
        # dropped = True
        logger.debug("dropped some history, history_start: %r, n_tokens: %r", history_start, n_tokens)
        if last:
            break
    # if dropped:
    #     fulltext = delim.join(history[history_start:]) + invitation
    logger.debug("fulltext: %r", fulltext)
    return fulltext, history_start


async def client_request(portal, input_text, config=None, timeout=None):
    """Call the core server and get a response."""

    req = await portal.prepare_request(config)

    req_input = req / "request.txt"
    req_input.write_text(input_text, encoding="utf-8")

    await portal.send_request(req)

    resp, status = await portal.wait_for_response(req, timeout=timeout)

    if status == "error":
        await portal.response_error(resp)  # raises RuntimeError?!

    new = resp / "new.txt"
    new_text = new.read_text(encoding="utf-8") if new.exists() else ""

    return new_text, resp  # , generated_text


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


async def run_search(agent, query, file, args, history, history_start, limit=True, mission=None, summary=None, config=None, num=10, agents=None):
    """Run a search agent."""
    name = agent.name
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

    logger.debug("query: %r %r", name, query)

    response = await search.search(query, engine=name, markdown=True, num=num, limit=limit, safe=not ADULT)
    response2 = f"{name}:\t\n{response}"
    logger.debug("response:\n%s", response2)
    response3 = fix_layout(response2, args, agent)
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

    while room_dir != top_dir:
        agents_dir = room_dir / "agents"
        if agents_dir.exists():
            agents_dirs.append(agents_dir)
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
    config = config_read(config_file)

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

    bots = conductor.who_should_respond(
        message,
        agents=agents,
        history=history_messages,
        default=welcome_agents,
        include_humans_for_ai_message=False,
        include_humans_for_human_message=True,
        mission=mission,
        config=config,
        room=room,
    )
#    logger.info("who should respond: %r", bots)

    # Support "directed-poke" which removes itself, like -@Ally
    # TODO this is a bit dodgy and has a race condition
    if message and message["content"].startswith("-@"):  # pylint: disable=unsubscriptable-object
        history_messages.pop()
        history.pop()
        room.undo("root")
        message = history_messages[-1] if history_messages else None

    count = 0
    for bot in bots:
        if not (bot and bot.lower() in agents.names()):
            continue

        agent = agents.get(bot.lower())

        # load agent's mission file, if present
        my_mission = mission.copy()
        agent_mission_file = room.find_agent_resource_file("m", bot.lower())
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
                agent, query, file, args, history, history_start=history_start, mission=my_mission, summary=summary, config=config, agents=agents
        )
        response = response.strip()

        if agent.get("narrator"):
            response = response.lstrip(f'{agent.name}:')
            # remove 1 tab from start of each line
            response = "\n".join([line[1:] if line.startswith("\t") else line for line in response.split("\n")])

        # If the previous message begins with - it was ephemeral, so remove it
        # TODO this might not work well when multiple bots respond
        if history and history[-1].startswith("-"):
            history.pop()
            history_messages.pop()
            room.undo("root")
            # sleep for a bit
            await asyncio.sleep(0.1)

        history.append(response)
        logger.debug("history 2: %r", history)
        # avoid re-processing in response to an AI response
        if skip is not None:
            logger.debug("Will skip processing after agent/s response: %r", file)
            skip[file] += 1
        chat.chat_write(file, history[-1:], delim=args.delim, invitation=args.delim)

        count += 1
    return count


async def run_agent(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None) -> str:
    """Run an agent."""
    function = agent["fn"]
    logger.debug("query: %r", query)
    return await function(agent, query, file, args, history, history_start=history_start, mission=mission, summary=summary, config=config, agents=agents)


async def local_agent(agent, _query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None) -> str:
    """Run a local agent."""
    # print("local_agent: %r %r %r %r %r %r", query, agent, file, args, history, history_start)

    if config is None:
        config = {}

    # Note: the invitation should not end with a space, or the model might use lots of emojis!
    name = agent.name
    name_lc = name.lower()

    # Allow to override agent settings in the config
    agent = agent.copy()
    if config and config.get("agents") and "all" in config["agents"]:
        agent.update(config["agents"]["all"])
    if config and config.get("agents") and name_lc in config["agents"]:
        agent.update(config["agents"][name_lc])

    logger.debug("Running local agent %r", agent)

    invitation = args.delim + name + ":"

    model_name = agent["model"]
    n_context = agent.get("context")
    if agent.get("type") in ["image_a1111", "safe_shell", "search"]:
        n_context = 1

    if n_context is not None:
        if n_context == 0:
            context = []
        else:
            context = history[-n_context:]
    else:
        context = history.copy()

    # remove "thinking" sections from context
    context = chat.context_remove_thinking_sections(context, agent)

    # missions
    include_mission = agent.get("type") != "image_a1111"  # TODO clean this

    image_agent = agent.get("type", "").startswith("image_")
    dumb_agent = agent.get("dumb", False)
    image_count = config.get("image_count", 1)

    if include_mission:
        # prepend mission / info / context
        # TODO try mission as a "system" message?
        context2 = []
        mission_pos = config.get("mission_pos", 0)
        logger.debug("mission_pos: %r", mission_pos)
        if summary:
            context2 += summary
        context2 += context
        if mission:
            context2.insert(mission_pos, "\n".join(mission))
        # put remote_messages[-1] through the input_maps
        context = context2

    apply_maps(agent["input_map"], agent["input_map_cs"], context)

    # add system messages
    system_top = agent.get("system_top")
    system_bottom = agent.get("system_bottom")
    age_number = agent.get("age")
    age = num2words(age_number) if age_number else None
    if age and system_top:
        system_top += f"\n\nYou are {age} years old"
    elif age and system_bottom:
        system_bottom += f"\n\nYou are {age} years old"
    elif age:
        logger.warning("age provided but no system message to add it to, for agent %r", agent.name)
    if system_bottom:
        n_messages = len(context)
        pos = agent.get("system_bottom_pos", 0)
        pos = min(pos, n_messages)
        system_bottom_role = agent.get("system_bottom_role", "System")
        if system_bottom_role:
            context.insert(n_messages - pos, f"{system_bottom_role}:\t{system_bottom}")
        else:
            context.insert(n_messages - pos, f"{system_bottom}")
        logger.debug("system_bottom: %r", system_bottom)
    if system_top:
        system_top_role = agent.get("system_top_role", None)
        context.insert(0, f"{system_top_role}:\t{system_top}")
        logger.debug("system_top: %r", system_top)

    logger.debug("context: %s", args.delim.join(context[-6:]))

    agent_name_esc = regex.escape(name)

    # preprocess markdown in messages for includes
    context_messages = [
        {
            "user": m.get("user"),
            "content": (await ally_markdown.preprocess(m["content"], file, m.get("user")))[0]
        }
        for m in bb_lib.lines_to_messages(context)]
    context = list(bb_lib.messages_to_lines(context_messages))

    need_clean_prompt = agent.get("clean_prompt", dumb_agent)
    if need_clean_prompt:
        fulltext = chat.clean_prompt(context, name, args.delim)
    else:
        fulltext, history_start = get_fulltext(args, model_name, context, history_start, invitation, args.delim)

    if "config" in agent:
        gen_config = agent["config"].copy()
        gen_config["model"] = model_name
        if image_agent:
            gen_config["count"] = image_count
    else:
        # load the config each time, in case it has changed
        # TODO the config should be per agent, not global
        gen_config = load_config(args)

    if "lines" in agent:
        gen_config["lines"] = agent["lines"]

    # TODO: These stop regexps don't yet handle names with spaces or punctuation.
    gen_config["stop_regexs"] = [
        # Allow the agent's own name (ignoring case) using a negative lookahead.
        # A line starting with a name starting with any letter, colon and whitespace.
        r"(?umi)^(?!" + agent_name_esc + r"\s*:)[\p{L}][\p{L}\p{N}_]*:\s*\Z",
        # A name beginning with upper-case letter followed by colon and TAB, anywhere in the line
        r"(?u)\b(?!" + agent_name_esc + r":)[\p{Lu}][\p{L}\p{N}_]*:\t",
    ]

    # If no history, stop after the first line always. It tends to run away otherwise.
    if not history or (len(history) == 1 and history[0].startswith("System:\t")):
        logger.debug("No history, will stop after the first line.")
        gen_config["stop_regexs"].append(r"\n")

    gen_config["stop_regexs"].extend(agent.get("stop_regexs", []))

    if image_agent:
        fulltext2 = add_configured_image_prompts(fulltext, [agent, config])
        logger.debug("fulltext after adding configured image prompts: %r", fulltext2)
    else:
        fulltext2 = fulltext

    service = agent["type"]

#     logger.info("service: %r", service)

    portal = portals.get_portal(service)

    logger.debug("fulltext: %r", fulltext2)
    logger.debug("config: %r", gen_config)
#     logger.info("portal: %r", str(portal.portal))

    response, resp = await client_request(portal, fulltext2, config=gen_config, timeout=LOCAL_AGENT_TIMEOUT)

    apply_maps(agent["output_map"], agent["output_map_cs"], [response])

    room = Room(path=Path(file))

    # try to get image seed from response
    image_seed = None
    image_metadata = {}
    try:
        # read result.yaml
        data = yaml.safe_load((resp / "result.yaml").read_text(encoding="utf-8"))
        image_seed = data["seed"]
        image_metadata = data["metadata"]
    except (FileNotFoundError, KeyError):
        pass

    image_alt_type = config.get("image_alt")

    # look for attachments, other files in resp/ in sorted order
    # service image_a1111 should return a file name in response
    for resp_file in sorted(resp.iterdir()):
        if resp_file.name in ["new.txt", "request.txt", "config.yaml", "log.txt", "result.yaml"]:
            continue

        text = ""
        if Path(resp_file).suffix in [".png", ".jpg"]:
            if image_seed is not None:
                text = f"#{image_seed} "
                image_seed += 1
            if image_alt_type == "raw_prompt" or not resp_file.stem in image_metadata:
                text += fulltext
            else:
                prompt = image_metadata[resp_file.stem]
                prompt = re.sub(r"^parameters: ", "", prompt)
                prompt = re.sub(r"\n+Steps:.*", "", prompt)
                prompt = re.sub(r"\n+Negative prompt: ", " NEGATIVE ", prompt)
                text += prompt

        name, _url, _medium, markdown, task = await chat.upload_file(room.name, agent.name, str(resp_file), alt=text or None)
        if task:
            add_task(task, f"upload post-processing: {name}")
        if response:
            response += " "
        else:
            response += "\n"
        response += markdown

    await portal.remove_response(resp)

    logger.debug("response: %r", response)

    agent_names = list(agents.names())
    history_messages = list(bb_lib.lines_to_messages(history))
    all_people = conductor.participants(history_messages)
    people_lc = list(map(str.lower, set(agent_names + all_people)))

    response = trim_response(response, args, agent.name, people_lc=people_lc)
    response = fix_layout(response, args, agent)

    if invitation:
        tidy_response = invitation.strip() + "\t" + response.strip()
    else:
        tidy_response = response

    # TODO accept attachments from model

    logger.debug("tidy response: %r", tidy_response)

    return tidy_response


def add_configured_image_prompts(fulltext, configs):
    """Add configured prompts to the fulltext."""
    splits = re.split(r"\s*\bNEGATIVE\b\s*", fulltext, maxsplit=1)
    if len(splits) == 2:
        positive, negative = splits
    else:
        positive = fulltext
        negative = ""
    mappings_1 = {}
    mappings = {}
    mappings_neg_1 = {}
    mappings_neg = {}
    for config in configs:
        if "image_prompt_map_1" in config:
            mappings_1 |= config["image_prompt_map_1"]
        if "image_prompt_map" in config:
            mappings |= config["image_prompt_map"]
        if "image_prompt_negative_map_1" in config:
            mappings_neg_1 |= config["image_prompt_negative_map_1"]
        if "image_prompt_negative_map" in config:
            mappings_neg |= config["image_prompt_negative_map"]
    positive = re_map.apply_mappings(positive, mappings, mappings_1)
    negative = re_map.apply_mappings(negative, mappings_neg, mappings_neg_1)

    for config in configs:
        if "image_prompt_template" in config:
            positive = str(config["image_prompt_template"]).replace("%s", positive)
        if "image_prompt_negative_template" in config:
            negative = str(config["image_prompt_negative_template"]).replace("%s", negative)
    positive = re.sub(r'\s\s+', ' ', positive.strip())
    negative = re.sub(r'\s\s+', ' ', negative.strip())
    fulltext = positive
    if negative:
        fulltext += "\nNEGATIVE\n" + negative

    return fulltext


def apply_maps(mapping, mapping_cs, context):
    """for each word in the mapping, replace it with the value"""

    logger.debug("apply_maps: %r %r", mapping, mapping_cs)

    if not (mapping or mapping_cs):
        return

    def map_word(match):
        """Map a word."""
        word = match.group(1)
        word_lc = word.lower()
        out = mapping_cs.get(word)
        if out is None:
            out = mapping.get(word_lc)
        if out is None:
            out = word
        return out

    for i, msg in enumerate(context):
        old = msg
        context[i] = re.sub(r"\b(.+?)\b", map_word, msg)
        if context[i] != old:
            logger.debug("map: %r -> %r", old, context[i])


async def remote_agent(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None) -> str:
    """Run a remote agent."""
    service = agent["type"]

    if config is None:
        config = {}

    name = agent.name
    name_lc = name.lower()

    # Allow to override agent settings in the config
    agent = agent.copy()
    if config and config.get("agents") and "all" in config["agents"]:
        agent.update(config["agents"]["all"])
    if config and config.get("agents") and name_lc in config["agents"]:
        agent.update(config["agents"][name_lc])

    logger.debug("Running remote agent %r", agent)

    n_context = agent["context"]
    if n_context is not None:
        if n_context == 0:
            context = []
        else:
            context = history[-n_context:]
    else:
        context = history.copy()

    # XXX history is a list of lines, not messages, so won't the context sometimes contain partial messages? Yuk. That will interact badly with missions, too.
    # hacky temporary fix here for now, seems to work:
    while context and context[0].startswith("\t"):
        logger.debug("removing partial message at start of context: %r", context[0])
        context.pop(0)

    # remove "thinking" sections from context
    context = chat.context_remove_thinking_sections(context, agent)

    # prepend mission / info / context
    # TODO try mission as a "system" message?
    context2 = []
    mission_pos = config.get("mission_pos", 0)
    if summary:
        context2 += f"System:\t{summary}"
    context2 += context
    if mission:
        context2.insert(mission_pos, "System:\t" + "\n".join(mission))
    # put remote_messages[-1] through the input_maps
    apply_maps(agent["input_map"], agent["input_map_cs"], context2)

    context_messages = list(bb_lib.lines_to_messages(context2))

    remote_messages = []

    # TODO images in system messages?
    await add_images_to_messages(file, context_messages, agent.get("images", 0))

    # preprocess markdown in messages for includes
    for m in context_messages:
        m["content"] = (await ally_markdown.preprocess(m["content"], file, m.get("user")))[0]

    # TODO Can't include from system messages, what user permission to use?

    # convert context_messages to remote_messages, with only user and assistant roles

    for msg in context_messages:
        logger.debug("msg1: %r", msg)
        u = msg.get("user")
        u_lc = u.lower() if u is not None else None
        # if u in agents_lc:
        content = msg["content"]
        if u_lc == agent.name.lower():
            role = "assistant"
        else:
            role = "user"
            if u:
                content = u + ": " + content
        msg2 = {
            "role": role,
            "content": content.rstrip(),
        }
        if "images" in msg:
            msg2["images"] = msg["images"]
        logger.debug("msg2: %r", msg2)
        remote_messages.append(msg2)

    if remote_messages and remote_messages[0]["role"] == "assistant" and agent["type"] in "anthropic":
        remote_messages.insert(0, {"role": "user", "content": "?"})

    # add system messages
    system_top = agent.get("system_top")
    system_bottom = agent.get("system_bottom")
    system_bottom_role = "user" if service == "google" else agent.get("system_bottom_role", "user")
    system_top_role = "user" if service == "google" else agent.get("system_top_role", "system")
    age_number = agent.get("age")
    age = num2words(age_number) if age_number else None
    if age and system_top:
        system_top += f"\n\nYou are {age} years old"
    elif age and system_bottom:
        system_bottom += f"\n\nYou are {age} years old"
    elif age:
        logger.warning("age provided but no system message to add it to, for agent %r", agent.name)
    if system_bottom:
        if system_bottom_role == "user":
            system_bottom = f"System: {system_bottom}"
        n_messages = len(remote_messages)
        pos = agent.get("system_bottom_pos", 0)
        pos = min(pos, n_messages)
        remote_messages.insert(n_messages - pos, {"role": system_bottom_role, "content": system_bottom.rstrip()})
    if system_top:
        if system_top_role == "user":
            system_top = f"System: {system_top}"
        remote_messages.insert(0, {"role": system_top_role, "content": system_top.rstrip()})

    # Some agents require alternating user and assistant messages. Mark most recent message as "user", then check backwards and cut off when no longer alternating.
    # TODO aggregate messages together so we can include everything
    if agent.get("alternating_context") and remote_messages:
        logger.debug("alternating_context")
        remote_messages[-1]["role"] = "user"
        system_messages = []
        while remote_messages[0]["role"] == "system":
            system_messages.append(remote_messages.pop(0)["content"])
        pos = len(remote_messages) - 2
        expect_role = "assistant"
        while pos >= 0:
            logger.debug("pos: %r, expect_role: %r, role: %r", pos, expect_role, remote_messages[pos]["role"])
            if remote_messages[pos]["role"] == "system":
                system_messages.append(remote_messages[pos]["content"])
                remote_messages.pop(pos)
                pos -= 1
                continue
            if remote_messages[pos]["role"] != expect_role:
                remote_messages = remote_messages[pos + 1 :]
                break
            expect_role = "user" if expect_role == "assistant" else "assistant"
            pos -= 1
        if remote_messages[0]["role"] != "user":
            remote_messages.insert(0, {"role": "user", "content": "Hi!"})
        if system_messages:
            remote_messages.insert(0, {"role": "system", "content": "\n\n".join(system_messages)})

    if agent["type"] == "anthropic" and not remote_messages or remote_messages[-1]["role"] == "assistant":
        remote_messages.append({"role": "user", "content": ""})

    opts = llm.Options(model=agent["model"])  # , indent="\t")
    for k, v in agent.get("options", {}).items():
        setattr(opts, k, v)

    # Some agents don't like empty content, specifically google
    if not remote_messages[-1]["content"]:
        remote_messages[-1]["content"] = "?"
    remote_messages = [m for m in remote_messages if m["content"]]

    # Set up stop sequences for other participants
    logger.debug("context_messages: %r", context_messages)
    all_people = conductor.all_participants(context_messages)
    if opts.stop is None:
        opts.stop = []
    for p in all_people:
        if p == agent.name:
            continue
        opts.stop.append(f"\n\n{p}: ")

    logger.debug("stop: %r", opts.stop)

    # import python pretty printer:
    from pprint import pformat

    logger.debug("remote_messages: %s", pformat(remote_messages))
    logger.debug("remote_messages: %s", json.dumps(remote_messages, indent=2))

    ###### the actual query ######
    logger.debug("querying %r = %r", agent.name, agent["model"])
    try:
        output_message = await llm.aretry(llm.allm_chat, REMOTE_AGENT_RETRIES, opts, remote_messages)
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("Exception during generation")
        return f"{agent.name}:\n" + re.sub(r'(?m)^', '\t', str(e))
    #google.generativeai.types.generation_types.StopCandidateException: finish_reason: PROHIBITED_CONTENT

    response = output_message["content"]
    box = [response]
    apply_maps(agent["output_map"], agent["output_map_cs"], box)
    response = box[0]

    if response.startswith(agent.name + ": "):
        logger.debug("stripping agent name from response")
        response = response[len(agent.name) + 2 :]

    # fix indentation for code
    if opts.indent:
        lines = response.splitlines()
        lines = tab.fix_indentation_list(lines, opts.indent)
        response = "".join(lines)

    logger.debug("response 1: %r", response)
    response = fix_layout(response, args, agent)
    logger.debug("response 2: %r", response)
    response = f'{agent.name}:\t{response.strip()}'
    logger.debug("response 3: %r", response)
    return response.rstrip()


async def add_images_to_messages(file:str, messages: list[Message], image_count_max: int) -> None:
    """Add images to a list of messages."""
    if not image_count_max:
        return messages

    image_url_pattern = r'''
        # First alternative: Markdown image syntax
        !             # Literal exclamation mark
        \[            # Opening square bracket
        [^]]*         # Any characters except closing bracket
        \]            # Closing square bracket
        \(            # Opening parenthesis
        (.*?)         # First capturing group: URL (non-greedy match)
        \)            # Closing parenthesis

        |             # OR

        # Second alternative: HTML image tag
        <img\s        # Opening img tag
        [^>]*?        # Any attributes before src (non-greedy)
        src="         # src attribute opening
        ([^"<>]*?)    # Second capturing group: URL (non-greedy match)
        "             # Closing quote
    '''

    logger.debug("Checking messages for images")

    message_count = 0
    image_count = 0

    for msg in reversed(messages):
        matches = re.findall(image_url_pattern, msg['content'], flags=re.VERBOSE | re.DOTALL | re.IGNORECASE)
        logger.debug("Checking message: %s", msg['content'])
        logger.debug("Matches: %s", matches)
        image_urls = [url for markdown_url, html_url in matches for url in (markdown_url, html_url) if url]

        logger.debug("Found image URLs: %s", image_urls)
        if not image_urls:
           continue

        # count messages having images
        message_count += 1

        msg['images'] = image_urls

        # TODO could fetch in parallel, likely not necessary
        # TODO could split text where images occur
        msg['images'] = [
            await ally_markdown.resolve_url_path(file, url, msg.get('user'), throw=False)
            for url
            in msg['images']]

        msg['images'] = [url for url in msg['images'] if url]

        # If we have too many images, take the first ones from the message
        space_left = image_count_max - image_count
        if len(msg['images']) > space_left:
            msg['images'] = msg['images'][:space_left]

        image_count += len(msg['images'])

        logger.debug("Message contains images: %s", msg['images'])

        if image_count >= image_count_max:
            break

#     logger.info("Found %d messages with %d images", message_count, image_count)


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


async def safe_shell(agent, query, file, args, history, history_start=0, command=None, mission=None, summary=None, config=None, agents=None):
    """Run a shell agent."""
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
    response3 = fix_layout(response2, args, agent)
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


active_tasks: dict[asyncio.Task, str] = {}


def add_task(task: asyncio.Task, description: str):
    """Add a task to the active tasks."""
    active_tasks[task] = description
    task.add_done_callback(task_done_callback)


def task_done_callback(task):
    """Callback for when a task is done."""
    logger.debug("Task done: %r", active_tasks[task])
    del active_tasks[task]
    try:
        task.result()
    except Exception:  # pylint: disable=broad-except
        logger.exception("Task failed", exc_info=True)


async def wait_for_tasks():
    """Wait for all active tasks to complete."""
    logger.info("Waiting for %d active tasks", len(active_tasks))
    while active_tasks:
        await asyncio.gather(*active_tasks.keys())


def list_active_tasks():
    """List the active tasks."""
    logger.info("Active tasks: %d", len(active_tasks))
    for description in active_tasks.values():
        logger.info("  - %s", description)


def check_file_type(path):
    """Check the file type, either room or agent."""
    ext = Path(path).suffix
    if ext == ".bb" and path.startswith(str(PATH_ROOMS)+"/"):
        return "room"
    if ext == ".yml" and path.startswith(str(PATH_AGENTS)+"/"):
        return "agent"
    return None


async def watch_loop(args):
    """Follow the watch log, and process files."""
    skip = defaultdict(int)

    agents = Agents(services)
    agents.load(PATH_AGENTS)
    agents.write_agents_list(PATH_ROOMS / ".agents.yml")

    async with atail.AsyncTail(filename=args.watch, follow=True, rewind=True) as queue:
        while (line := await queue.get()) is not None:
            try:
                file_path, change_type, old_size, new_size = line.rstrip("\n").split("\t")
                change_type = Change(int(change_type))
                old_size = int(old_size) if old_size != "" else None
                new_size = int(new_size) if new_size != "" else None

                file_type = check_file_type(file_path)
                if file_type == "room":
                    # Create and track the task
                    task = asyncio.create_task(file_changed(file_path, change_type, old_size, new_size, args, skip, agents))
                    add_task(task, f"file changed: {file_path}")
                    list_active_tasks()
                elif file_type == "agent":
                    agents.handle_file_change(file_path, change_type)
                    agents.write_agents_list(PATH_ROOMS / ".agents.yml")
                else:
                    logger.debug("Ignoring change to file: %r", file_path)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Error processing file change", exc_info=True)
            finally:
                queue.task_done()


async def restart_service():
    """Restart the service."""
    await wait_for_tasks()
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


def load_config(args):
    """Load the generations config file."""
    config = {}
    if args.config:
        with open(args.config, encoding="utf-8") as f:
            settings = yaml.load(f, Loader=yaml.FullLoader)
        for k, v in settings.items():
            config[k] = v
    if not config:
        config = None
    return config


def load_model_tokenizer(args):
    """Load the model tokenizer."""
    models_dir = PATH_MODELS / "llm"
    model_path = Path(models_dir) / args.model
    if args.model and not model_path.exists() and args.model.endswith(".gguf"):
        args.model = args.model[: -len(".gguf")]
        model_path = Path(models_dir) / args.model
    logger.debug("model_path: %r", model_path)
    if args.model and model_path.exists():
        # This will block, but it doesn't matter because this is the init for the program.
        return load_tokenizer(model_path)
    return None


services = {
    "llm_llama":    {"link": "portal", "fn": local_agent},
    "image_a1111":  {"link": "portal", "fn": local_agent, "dumb": True},
    "openai":       {"link": "remote", "fn": remote_agent},
    "anthropic":    {"link": "remote", "fn": remote_agent},
    "google":       {"link": "remote", "fn": remote_agent},
    "perplexity":   {"link": "remote", "fn": remote_agent},
    "xai":          {"link": "remote", "fn": remote_agent},
    "deepseek":     {"link": "remote", "fn": remote_agent},
    "openrouter":   {"link": "remote", "fn": remote_agent},
    "safe_shell":   {"link": "tool", "fn": safe_shell, "safe": False, "dumb": True},  # ironically
    "search":       {"link": "tool", "fn": run_search, "dumb": True},
}


def get_opts():  # pylint: disable=too-many-statements
    """Get the command line options."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    modes_group = parser.add_argument_group("Modes of operation")
    modes_group.add_argument("--watch", "-w", default=None, help="Watch mode, follow a watch log file")

    watch_group = parser.add_argument_group("Watch mode options")
    watch_group.add_argument("--ext", default=DEFAULT_FILE_EXTENSION, help="File extension to watch for")
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

    TOKENIZERS[args.model] = load_model_tokenizer(args)

    logger.info("Watching chat rooms")
    asyncio.create_task(restart_if_code_changes())
    await watch_loop(args)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("interrupted")
        sys.exit(0)
