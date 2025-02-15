#!/usr/bin/env python3-allemande

""" Ally Chat / Electric Barbarella v8 - multi-user LLM chat app """

import os
import sys
import time
import argparse
import logging
from math import inf
from pathlib import Path
import re
import subprocess
from types import SimpleNamespace
import asyncio
from collections import defaultdict
import json
import importlib

import shlex
import readline
from watchfiles import Change
import yaml
import regex

import ucm
import conductor
import search
import tab
import chat
import agents
import llm
from ally import portals
import atail
from safety import safety

# The last modification time of reloadable modules
_last_modified = {}


def reload_if_modified(module_name):
    """
    Checks if the specified module's source file has been modified,
    and reloads it if it has changed.

    Args:
        module_name (str): Name of the module to check and potentially reload

    Returns:
        bool: True if module was reloaded, False otherwise
    """
    try:
        # Get the module object
        module = sys.modules[module_name]

        # Get the path to the module's source file
        module_file = module.__file__

        # Get the current modification time
        current_mtime = os.path.getmtime(module_file)

        # Get the last recorded modification time, if any
        last_mtime = _last_modified.get(module_name, 0)

        # If the file has been modified since last check
        if current_mtime > last_mtime:
            # Reload the module
            importlib.reload(module)

            # Update the last modification time
            _last_modified[module_name] = current_mtime

            logger.warning(f"Module {module_name} has been reloaded.")
            return True

        return False

    except Exception as e:
        logger.error(f"Error reloading module {module_name}: {str(e)}")
        return False


os.environ["TRANSFORMERS_OFFLINE"] = "1"
import transformers  # pylint: disable=wrong-import-position, wrong-import-order


logger = logging.getLogger(__name__)

LOCAL_AGENT_TIMEOUT = 5 * 60


# TODO can't select model from here now

models = {
    "default": {
        "abbrev": "llama3",
        "description": "Meta-Llama-3.1-8B-Instruct",
        "cost": 0,
    },
}

first_model = next(iter(models.keys()))
default_model = os.environ.get("BB_MODEL", first_model)

DEFAULT_FILE_EXTENSION = "bb"


AGENTS = {}

TOKENIZERS = {}

REMOTE_AGENT_RETRIES = 3

MAX_REPLIES = 1

ADULT = True

UNSAFE = True


def load_agents():
    """Load the agents, if modified."""
    if reload_if_modified("agents"):
        register_all_agents()


def register_agents(agent_type, agents_dict, async_func):
    """Register agents"""

    async def agent_wrapper(agent, *args, **kwargs):
        """Wrapper for async agents"""
        return await async_func(agent, *args, **kwargs)

    def make_agent(agent_base, agent_name):
        """Make an agent"""
        agent = agent_base.copy()
        agent["fn"] = lambda *args, **kwargs: agent_wrapper(agent, *args, **kwargs)
        agent["type"] = agent_type
        if "name" not in agent:
            agent["name"] = agent_name
        return agent

    for agent_name, agent_base in agents_dict.items():
        agent_lc = agent_name.lower()
        agent = AGENTS[agent_lc] = make_agent(agent_base, agent_name)
        name_lc = agent["name"].lower()
        if name_lc != agent_lc:
            AGENTS[name_lc] = agent


def setup_agent_maps():
    """Setup maps for all agents"""
    for _agent_name, agent in AGENTS.items():
        setup_maps_for_agent(agent)


def setup_maps_for_agent(agent):
    """Setup maps for an agent"""
    for k in "input_map", "output_map", "map", "map_cs", "input_map_cs", "output_map_cs":
        if k not in agent:
            agent[k] = {}
    for k, v in agent["input_map"].items():
        k_lc = k.lower()
        if k == k_lc:
            continue
        del agent["input_map"][k]
        agent["input_map"][k_lc] = v
    for k, v in agent["output_map"].items():
        k_lc = k.lower()
        if k == k_lc:
            continue
        del agent["output_map"][k]
        agent["output_map"][k_lc] = v
    for k, v in agent["map"].items():
        k_lc = k.lower()
        v_lc = v.lower()
        if k_lc not in agent["input_map"]:
            agent["input_map"][k_lc] = v
        if v_lc not in agent["output_map"]:
            agent["output_map"][v_lc] = k
    for k, v in agent["map_cs"].items():
        if k not in agent["input_map_cs"]:
            agent["input_map_cs"][k] = v
        if v not in agent["output_map_cs"]:
            agent["output_map_cs"][v] = k


def register_all_agents():
    """Register agents"""
    global AGENTS
    AGENTS.clear()

    register_agents("local", agents.AGENTS_LOCAL, local_agent)
    register_agents("remote", agents.AGENTS_REMOTE, remote_agent)

    if UNSAFE:
        register_agents("tool", agents.AGENTS_PROGRAMMING, safe_shell)

    register_agents("tool", {agent: {"name": agent} for agent in search.agents}, run_search)

    if not ADULT:
        # remove any agent with "adult" attribute true
        AGENTS = {key: value for key, value in AGENTS.items() if not value.get("adult")}

    AGENTS = safety.apply_or_remove_adult_options(AGENTS, ADULT)

    setup_agent_maps()


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
    response = re.sub(r"^\s*" + agent_name_esc + r"\s*:\s(.*)", r"\1", response, flags=re.MULTILINE)

    # remove anything after a known person's name
    response = re.sub(r"(\n\s*(\w+)\s*:\s*(.*))", check_person_remove, response, flags=re.DOTALL)

    # response = re.sub(r"\n(##|<nooutput>|<noinput>|#GPTModelOutput|#End of output|\*/\n\n// End of dialogue //|// end of output //|### Output:|\\iend{code})(\n.*|$)", "", response , flags=re.DOTALL|re.IGNORECASE)

    if response != response_before:
        logger.warning("Trimmed response: %r\nto: %r", response_before, response)

    response = " " + response.strip()
    return response


def leading_spaces(text):
    """Return the number of leading spaces in a text."""
    return re.match(r"\s*", text).group(0)


def fix_layout(response, _args):
    """Fix the layout and indentation of the response."""
    lines = response.strip().split("\n")
    out = []
    in_table = False
    in_code = False

    # clean up the lines
    for i, line in enumerate(lines):
        # markdown tables must have a blank line before them ...
        if not in_table and ("---" in line or re.search(r"\|.*\|", line)):
            if i > 0 and lines[i - 1].strip():
                out.append("\t")
            in_table = True

        if in_table and not line.strip():
            in_table = False

        # detect if in_code
        if not in_code and re.search(r"```", line):
            in_code = True
            line1 = line
            if i == 0:
                line1 = re.sub(r"^[^\t]*", "", line1)
            base_indent = leading_spaces(line1)
        elif in_code and re.search(r"```", line):
            in_code = False

        if in_code:
            # For code, try to remove base_indent from the start of the line
            if base_indent and line.startswith(base_indent):
                line = line[len(base_indent) :]
            else:
                base_indent = ""
            if i > 0 and not base_indent:
                line = "\t" + line
        else:
            # For non-code, strip all leading tabs and trailing whitespace, to avoid issues
            line = "\t" + line.lstrip("\t").rstrip()

        out.append(line)

    response = ("\n".join(out)).rstrip()

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
            logger.info("guessing how many tokens to drop...")
            logger.info("  args.memory: %r", args.memory)
            logger.info("  n_tokens: %r", n_tokens)
            logger.info("  len(history): %r", len(history))
            logger.info("  history_start: %r", history_start)
            guess = ((n_tokens - args.memory) / n_tokens) * (len(history) - history_start)
            guess = int(guess * 0.7)
            logger.info("  guess: %r", guess)
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


async def run_search(agent, query, file, args, history, history_start, limit=True, mission=None, summary=None, config=None):
    """Run a search agent."""
    name = agent["name"]
    logger.debug("history: %r", history)
    history_messages = list(chat.lines_to_messages(history))
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
    query = re.sub(r"(show me|search( for|up)?|find( me)?|look( for| up)?|what(\'s| is) (the|a|an)?)\s+", "", query, re.IGNORECASE)
    logger.debug("query 4: %r", query)
    query = re.sub(r"#.*", "", query)
    logger.debug("query 5: %r", query)
    query = re.sub(r"[^\x00-~]", "", query)  # filter out emojis
    logger.debug("query 6: %r", query)
    query = re.sub(r"^\s*[,;.]|[,;.]\s*$", "", query).strip()

    logger.info("query: %r %r", name, query)

    # TODO make the search library async too
    async def async_search(query, name, limit):
        """Run a search in a thread."""
        return await asyncio.to_thread(search.search, query, engine=name, markdown=True, limit=limit)

    response = await async_search(query, name, limit)
    response2 = f"{name}:\t{response}"
    response3 = fix_layout(response2, args)
    logger.debug("response3:\n%s", response3)

    # wrap secondary divs in <details>
    response4 = re.sub(
        r"(</div>\n?\s*)(<div\b.*)",
        r"""\1<details class="up"><summary>more</summary>\n\2</details>\n""",
        response3,
        flags=re.DOTALL,
    )

    return response4


async def process_file(file, args, history_start=0, skip=None) -> int:
    """Process a file, return True if appended new content."""
    logger.info("Processing %s", file)

    history = chat.chat_read(file, args)

    history_count = len(history)

    # Load mission file, if present
    mission_file = re.sub(r"\.bb$", ".m", file)

    mission = chat.chat_read(mission_file, args)

    # Load summary file, if present
    summary_file = re.sub(r"\.bb$", ".s", file)
    summary = summary_read(summary_file, args)

    # Load config file, if present
    config_file = re.sub(r"\.bb$", ".yml", file)
    config = config_read(config_file)

    # logger.warning("loaded mission: %r", mission)
    # logger.warning("loaded history: %r", history)

    # get latest user name and bot name from history
    # bots = agents.AGENT_DEFAULT.copy()
    # if history:

    history_messages = list(chat.lines_to_messages(history))

    # TODO distinguish poke (only AIs and tools respond) vs posted message (humans might be notified)
    message = history_messages[-1] if history_messages else None

    bots = conductor.who_should_respond(
        message,
        agents=AGENTS,
        history=history_messages,
        default=agents.AGENT_DEFAULT,
        include_humans_for_ai_message=False,
        include_humans_for_human_message=True,
        mission=mission,
        direct_reply_chance=config.get("direct_reply_chance", 1.0),
    )
    logger.info("who should respond: %r", bots)

    # Support "directed-poke" which removes itself, like -@Ally
    # TODO this is a bit dodgy and has a race condition
    if message and message["content"].startswith("-@"):
        history_messages.pop()
        room = chat.Room(path=Path(file))
        room.undo("root")
        message = history_messages[-1] if history_messages else None

    count = 0
    for bot in bots:
        if not (bot and bot.lower() in AGENTS):
            continue

        agent = AGENTS[bot.lower()]

        #     - query is not even used in remote_agent
        if history:
            query1 = history[-1]
        else:
            query1 = agent.get("starter_prompt", agents.STARTER_PROMPT) or ""
            query1 = query1.format(bot=bot) or None
            history = [query1]
        logger.debug("query1: %r", query1)
        messages = list(chat.lines_to_messages([query1]))
        query = messages[-1]["content"] if messages else None

        logger.debug("query: %r", query)
        logger.debug("history 1: %r", history)
        response = await run_agent(agent, query, file, args, history, history_start=history_start, mission=mission, summary=summary, config=config)
        history.append(response)
        logger.debug("history 2: %r", history)
        # avoid re-processing in response to an AI response
        if skip is not None:
            logger.debug("Will skip processing after agent/s response: %r", file)
            skip[file] += 1
        chat.chat_write(file, history[-1:], delim=args.delim, invitation=args.delim)

        count += 1
    return count


async def run_agent(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None):
    """Run an agent."""
    function = agent["fn"]
    logger.debug("query: %r", query)
    return await function(query, file, args, history, history_start=history_start, mission=mission, summary=summary, config=config)


async def local_agent(agent, _query, file, args, history, history_start=0, mission=None, summary=None, config=None):
    """Run a local agent."""
    # print("local_agent: %r %r %r %r %r %r", query, agent, file, args, history, history_start)

    # Note: the invitation should not end with a space, or the model might use lots of emojis!
    name = agent["name"]
    invitation = args.delim + name + ":"

    model_name = agent["model"]
    n_context = agent.get("default_context")
    if n_context is not None:
        context = history[-n_context:]
    else:
        context = history.copy()

    # remove "thinking" sections from context
    context_remove_thinking_sections(context, agent["name"])

    # missions
    include_mission = agent.get("service") != "image_a1111"  # TODO clean this

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
    if system_bottom:
        n_messages = len(context)
        pos = agent.get("system_bottom_pos", 0)
        pos = min(pos, n_messages)
        system_bottom_role = agent.get("system_bottom_role", "System")
        if system_bottom_role:
            context.insert(n_messages - pos, f"{system_bottom_role}:\t{system_bottom}")
        else:
            context.insert(n_messages - pos, f"{system_bottom}")
    if system_top:
        system_top_role = agent.get("system_top_role", None)
        context.insert(0, f"{system_top_role}:\t{system_top}")

    logger.info("context: %s", args.delim.join(context[-6:]))

    agent_name_esc = regex.escape(name)

    def clean_image_prompt(context, agent_name_esc):
        """Clean the prompt for image gen agents."""

        # Remove everything before and including tab characters from each line in the context
        context = [regex.sub(r".*?\t", r"", line).strip() for line in context]

        # Join all lines in context with the specified delimiter
        text = args.delim.join(context)

        # Remove the first occurrence of the agent's name (case insensitive) and any following punctuation
        text = regex.sub(r".*\b" + agent_name_esc + r"\b[,;.!]*", r"", text, flags=regex.DOTALL | regex.IGNORECASE, count=1)

        # Remove the first pair of triple backticks and keep only the content between them
        text = re.sub(r"```(.*?)```", r"\1", text, flags=re.DOTALL, count=1)

        # Remove leading and trailing whitespace
        text = text.strip()

        logger.info("clean_image_prompt: after: %s", text)
        return text

    clean_prompt = agent.get("clean_prompt", False)
    if clean_prompt:
        fulltext = clean_image_prompt(context, agent_name_esc)
    else:
        fulltext, history_start = get_fulltext(args, model_name, context, history_start, invitation, args.delim)

    if "config" in agent:
        gen_config = agent["config"].copy()
        gen_config["model"] = model_name
    else:
        # load the config each time, in case it has changed
        # TODO the config should be per agent, not global
        gen_config = load_config(args)

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

    service = agent["service"]

    portal = portals.get_portal(service)

    logger.debug("fulltext: %r", fulltext)
    logger.debug("config: %r", gen_config)
    logger.debug("portal: %r", str(portal.portal))

    response, resp = await client_request(portal, fulltext, config=gen_config, timeout=LOCAL_AGENT_TIMEOUT)

    apply_maps(agent["output_map"], agent["output_map_cs"], [response])

    room = chat.Room(path=Path(file))

    # look for attachments, other files in resp/ in sorted order
    for resp_file in sorted(resp.iterdir()):
        if resp_file.name in ["new.txt", "request.txt", "config.yaml", "log.txt"]:
            continue
        name, url, medium, markdown, task = await chat.upload_file(room.name, agent["name"], str(resp_file), alt=fulltext)
        if response:
            response += f"\n\n"
        response += markdown

    await portal.remove_response(resp)

    logger.debug("response: %r", response)

    agent_names = list(AGENTS.keys())
    history_messages = list(chat.lines_to_messages(history))
    all_people = conductor.participants(history_messages)
    people_lc = list(map(str.lower, set(agent_names + all_people)))

    response = trim_response(response, args, agent["name"], people_lc=people_lc)
    response = fix_layout(response, args)

    if invitation:
        tidy_response = invitation.strip() + "\t" + response.strip()
    else:
        tidy_response = response

    # TODO accept attachments from model

    logger.debug("tidy response: %r", tidy_response)

    return tidy_response


def context_remove_thinking_sections(context: list[str], agent_name: str):
    """Remove "thinking" sections from the context."""
    # Remove any "thinking" sections from the context
    # A "thinking" section is a <details> block

    for i, message in enumerate(context):
        if message.startswith(agent_name + ":\t"):
            continue
        modified = re.sub(
            r"""(?ix)
            <details\b[^>]*>
            .*?
            (</details>|$)
            """,
            "",
            message,
            flags=re.DOTALL,
        )
        if modified != message:
            context[i] = modified
            logger.info("Removed 'thinking' section/s from message: %r", modified)


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


async def remote_agent(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None):
    """Run a remote agent."""
    n_context = agent["default_context"]
    context = history[-n_context:]
    # XXX history is a list of lines, not messages, so won't the context sometimes contain partial messages? Yuk. That will interact badly with missions, too.
    # hacky temporary fix here for now, seems to work:
    while context and context[0].startswith("\t"):
        logger.debug("removing partial message at start of context: %r", context[0])
        context.pop(0)

    # remove "thinking" sections from context
    context_remove_thinking_sections(context, agent["name"])

    # prepend mission / info / context
    # TODO try mission as a "system" message?
    context2 = []
    mission_pos = config.get("mission_pos", 0)
    if summary:
        context2 += f"System:\t{summary}"
    context2 += context
    if mission:
        context2.insert(mission_pos, "\n".join(mission))
    # put remote_messages[-1] through the input_maps
    apply_maps(agent["input_map"], agent["input_map_cs"], context2)

    context_messages = list(chat.lines_to_messages(context2))

    remote_messages = []

    # agent_names = list(AGENTS.keys())
    # agents_lc = list(map(str.lower, agent_names))

    for msg in context_messages:
        logger.debug("msg1: %r", msg)
        u = msg.get("user")
        u_lc = u.lower() if u is not None else None
        # if u in agents_lc:
        content = msg["content"]
        if u_lc == agent["name"].lower():
            role = "assistant"
        else:
            role = "user"
            if u:
                content = u + ": " + content
        msg2 = {
            "role": role,
            "content": content,
        }
        logger.debug("msg2: %r", msg2)
        remote_messages.append(msg2)

    while remote_messages and remote_messages[0]["role"] == "assistant" and "claude" in agent["model"]:
        remote_messages.pop(0)

    # add system messages
    system_top = agent.get("system_top")
    system_bottom = agent.get("system_bottom")
    if system_bottom:
        n_messages = len(remote_messages)
        pos = agent.get("system_bottom_pos", 0)
        pos = min(pos, n_messages)
        system_bottom_role = agent.get("system_bottom_role", "user")
        remote_messages.insert(n_messages - pos, {"role": system_bottom_role, "content": system_bottom})
    if system_top:
        system_top_role = agent.get("system_top_role", "system")
        remote_messages.insert(0, {"role": system_top_role, "content": system_top})

    # Some agents require alternating user and assistant messages. Mark most recent message as "user", then check backwards and cut off when no longer alternating.
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

    # TODO this is a bit dodgy and won't work with async
    opts = {
        "model": agent["model"],
        "indent": "\t",
    }
    llm.set_opts(opts)

    logger.debug("DEBUG: remote_messages: %s", json.dumps(remote_messages, indent=2))

    logger.debug("querying %r = %r", agent["name"], agent["model"])
    output_message = await llm.aretry(llm.allm_chat, REMOTE_AGENT_RETRIES, remote_messages)

    response = output_message["content"]
    box = [response]
    apply_maps(agent["output_map"], agent["output_map_cs"], box)
    response = box[0]

    if response.startswith(agent["name"] + ": "):
        logger.debug("stripping agent name from response")
        response = response[len(agent["name"]) + 2 :]

    # fix indentation for code
    if opts["indent"]:
        lines = response.splitlines()
        lines = tab.fix_indentation_list(lines, opts["indent"])
        response = "".join(lines)

    logger.debug("response 1: %r", response)
    response = fix_layout(response, args)
    logger.debug("response 2: %r", response)
    response = f"{agent['name']}:\t{response.strip()}"
    logger.debug("response 3: %r", response)
    return response.rstrip()


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


async def safe_shell(agent, query, file, args, history, history_start=0, command=None, mission=None, summary=None, config=None):
    """Run a shell agent."""
    name = agent["name"]
    logger.debug("history: %r", history)
    history_messages = list(chat.lines_to_messages(history))
    logger.debug("history_messages: %r", history_messages)
    message = history_messages[-1]
    query = message["content"]
    logger.debug("query 1: %r", query)
    rx = r"((ok|okay|hey|hi|ho|yo|hello|hola)\s)*\b" + re.escape(name) + r"\b"
    logger.debug("rx: %r", rx)
    query = re.sub(rx, "", query, flags=re.IGNORECASE)
    logger.debug("query 2: %r", query)
    query = re.sub(r"^\s*[,;.]|\s*$", "", query).strip()
    logger.debug("query 3: %r", query)

    # shell escape in python
    agent["command"]
    cmd_str = ". ~/.profile ; "
    cmd_str += " ".join(map(shlex.quote, agent["command"]))

    command = ["sshc", "allemande-nobody@localhost", "bash", "-c", cmd_str]
    agent["command"]

    # echo the query to the subprocess
    output, errors, status = await run_subprocess(command, query)

    # format the response
    response = ""
    if errors or status:
        response += "\n## status:\n" + str(status) + "\n\n"
        response += "## errors:\n```\n" + errors + "\n```\n\n"
        response += "## output:\n"
    response += "```\n" + output + "\n```\n"

    response2 = f"{name}:\t{response}"
    response3 = fix_layout(response2, args)
    logger.debug("response3:\n%s", response3)
    return response3


async def file_changed(file_path, change_type, old_size, new_size, args, skip):
    """Process a file change."""
    if args.ext and not file_path.endswith(args.ext):
        return
    if change_type == Change.deleted:
        return
    if not args.shrink and old_size and new_size < old_size:
        return
    if old_size is None:
        return
#     if new_size == 0 and old_size != 0:
#         return

    if skip.get(file_path):
        logger.debug("Won't react to AI response: %r", file_path)
        skip[file_path] -= 1
        return

    responded_count = 0
    try:
        logger.info("Processing file: %r", file_path)
        await process_file(file_path, args, skip=skip)
    except Exception as e:
        logger.exception("Processing file failed", exc_info=True)


async def watch_loop(args):
    """Follow the watch log, and process files."""

    skip = defaultdict(int)

    async with atail.AsyncTail(filename=args.watch, follow=True, rewind=True) as queue:
        while (line := await queue.get()) is not None:
            # Load the agents, if modified
            load_agents()

            try:
                file_path, change_type, old_size, new_size = line.rstrip("\n").split("\t")
                change_type = Change(int(change_type))
                old_size = int(old_size) if old_size != "" else None
                new_size = int(new_size) if new_size != "" else None

                # Process the change in a background coroutine,
                # so we can handle other changes concurrently.
                asyncio.create_task(file_changed(file_path, change_type, old_size, new_size, args, skip))
            finally:
                queue.task_done()


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
    models_dir = Path(os.environ["ALLEMANDE_MODELS"]) / "llm"
    model_path = Path(models_dir) / args.model
    if args.model and not model_path.exists() and args.model.endswith(".gguf"):
        args.model = args.model[: -len(".gguf")]
        model_path = Path(models_dir) / args.model
    logger.info("model_path: %r", model_path)
    if args.model and model_path.exists():
        # This will block, but it doesn't matter because this is the init for the program.
        return load_tokenizer(model_path)
    return None


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

    TOKENIZERS[args.model] = load_model_tokenizer(args)

    if not args.watch:
        raise ValueError("Watch file not specified")

    logger.info("Watching")
    await watch_loop(args)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("interrupted")
        sys.exit(0)
