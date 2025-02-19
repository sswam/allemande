#!/usr/bin/env python3-allemande
# pylint: disable=unused-argument

""" Ally Chat / Electric Barbarella v1.0.9 - multi-user LLM chat app """

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

import shlex
from watchfiles import awatch, Change
import yaml
import regex

import atail  # type: ignore
import ucm  # type: ignore
import conductor
import search  # type: ignore
import tab  # type: ignore
import chat
import llm  # type: ignore
from ally import portals  # type: ignore
from safety import safety  # type: ignore
from ally.cache import cache  # type: ignore

os.environ["TRANSFORMERS_OFFLINE"] = "1"
import transformers  # type: ignore # pylint: disable=wrong-import-position, wrong-import-order

PATH_HOME   = Path(os.environ["ALLEMANDE_HOME"])
PATH_ROOMS  = Path(os.environ["ALLEMANDE_ROOMS"])
PATH_AGENTS = Path(os.environ["ALLEMANDE_AGENTS"])
PATH_VISUAL = Path(os.environ["ALLEMANDE_VISUAL"])
PATH_MODELS = Path(os.environ["ALLEMANDE_MODELS"])
# TODO put agents dir in rooms?

# TODO put some of these settings in a global reloadable config files
STARTER_PROMPT = """System:\tPlease briefly greet the user or start a conversation, in one line. You can creative, or vanilla."""

logger = logging.getLogger(__name__)
logging.getLogger('watchfiles').setLevel(logging.WARNING)

LOCAL_AGENT_TIMEOUT = 5 * 60  # 5 minutes

DEFAULT_FILE_EXTENSION = "bb"

REMOTE_AGENT_RETRIES = 3

MAX_REPLIES = 1

ADULT = True

SAFE = False

TOKENIZERS: dict[str, transformers.AutoTokenizer] = {}


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


Agent = dict[str, Any]


def set_up_agent(agent: Agent) -> Agent:
    """Set up an agent"""

    agent_type = agent["type"]
    if agent_type in ["human", "visual"]:
        return None

    service = services.get(agent_type)

    if service is None:
        raise ValueError(f'Unknown service for agent: {agent["name"]}, {agent["type"]}')
    if "safe" in service:
        agent["safe"] = service["safe"]

    if SAFE and not agent.get("safe", True):
        raise ValueError(f'Unsafe agent {agent["name"]} not allowed in safe mode')

    if not ADULT and agent.get("adult"):
        raise ValueError(f'Adult agent {agent["name"]} only allowed in adult mode')

    agent["type"] = service["type"]
    agent["fn"] = service["fn"]

    # replace $NAME, $FULLNAME and $ALIAS in the agent's prompts
    for prompt_key in "system_top", "system_bottom":
        prompt = agent.get(prompt_key)
        if not prompt:
            continue
        name = agent["name"]
        fullname = agent.get("fullname", name)
        aliases = agent.get("aliases") or [name]
        aliases_or = ", ".join(aliases[:-1]) + " or " + aliases[-1] if len(aliases) > 1 else aliases[0]
        prompt = re.sub(r"\$NAME\b", name, prompt)
        prompt = re.sub(r"\$FULLNAME\b", fullname, prompt)
        prompt = re.sub(r"\$ALIAS\b", aliases_or, prompt)
        agent[prompt_key] = prompt

    agent = safety.apply_or_remove_adult_options(agent, ADULT)

    setup_maps_for_agent(agent)

    return agent


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


def fix_layout(response, _args, agent):
    """Fix the layout and indentation of the response."""
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
            line = line.lstrip("\t").rstrip()
            if i > 0:
                line = "\t" + line

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


async def run_search(agent, query, file, args, history, history_start, limit=True, mission=None, summary=None, config=None, max_results=10, agents=None):
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
    async def async_search():
        """Run a search in a thread."""
        return await asyncio.to_thread(search.search, query, engine=name, markdown=True, limit=limit, max_results=max_results)

    response = await async_search()
    response2 = f"{name}:\t{response}"
    response3 = fix_layout(response2, args, agent)
    logger.info("response3:\n%s", response3)

    # wrap secondary divs in <details>
    response4 = re.sub(
        r"(</div>\n?\s*)(<div\b.*)",
        r"""\1<details class="search"><summary>more</summary>\n\t\2</details>\n""",
        response3,
        flags=re.DOTALL,
    )

    logger.info("response4:\n%s", response3)

    return response4


def find_resource_file(file, ext, name=None):
    """Find a resource file for the chat room."""
    parent = Path(file).parent
    stem = Path(file).stem
    resource = parent / (stem + "." + ext)
    if not resource.exists():
        stem_no_num = re.sub(r"-\d+$", "", stem)
        if stem_no_num != stem:
            resource = parent / (stem_no_num + "." + ext)
    if not resource.exists():
        resource = parent / (name + "." + ext)
    if not resource.exists():
        resource = None
    return str(resource) if resource else None


async def process_file(file, args, history_start=0, skip=None, agents=None) -> int:
    """Process a file, return True if appended new content."""
    logger.info("Processing %s", file)

    history = chat.chat_read(file, args)

    # Load mission file, if present
    mission_file = find_resource_file(file, "m", "mission")
    mission = chat.chat_read(mission_file, args)

    # Load summary file, if present
    summary_file = find_resource_file(file, "s", "summary")
    summary = summary_read(summary_file, args)

    # Load config file, if present
    config_file = find_resource_file(file, "yml", "config")
    config = config_read(config_file)

    history_messages = list(chat.lines_to_messages(history))

    # TODO distinguish poke (only AIs and tools respond) vs posted message (humans might be notified)
    message = history_messages[-1] if history_messages else None

    welcome_agents = [name for name, agent in agents.items() if agent.get("welcome")]

    bots = conductor.who_should_respond(
        message,
        agents_dict=agents,
        history=history_messages,
        default=welcome_agents,
        include_humans_for_ai_message=False,
        include_humans_for_human_message=True,
        mission=mission,
        config=config,
    )
    logger.info("who should respond: %r", bots)

    # Support "directed-poke" which removes itself, like -@Ally
    # TODO this is a bit dodgy and has a race condition
    if message and message["content"].startswith("-@"):  # pylint: disable=unsubscriptable-object
        history_messages.pop()
        room = chat.Room(path=Path(file))
        room.undo("root")
        message = history_messages[-1] if history_messages else None

    count = 0
    for bot in bots:
        if not (bot and bot.lower() in agents):
            continue

        agent = agents[bot.lower()]

        #     - query is not even used in remote_agent
        if history:
            query1 = history[-1]
        else:
            query1 = agent.get("starter_prompt", STARTER_PROMPT) or ""
            query1 = query1.format(bot=bot) or None
            history = [query1]
        logger.debug("query1: %r", query1)
        messages = list(chat.lines_to_messages([query1]))
        query = messages[-1]["content"] if messages else None

        logger.debug("query: %r", query)
        logger.debug("history 1: %r", history)
        response = await run_agent(
            agent, query, file, args, history, history_start=history_start, mission=mission, summary=summary, config=config, agents=agents
        )
        response = response.strip()
        if agent.get("narrator"):
            response = response.lstrip(f'{agent["name"]}:\t')

        history.append(response)
        logger.debug("history 2: %r", history)
        # avoid re-processing in response to an AI response
        if skip is not None:
            logger.debug("Will skip processing after agent/s response: %r", file)
            skip[file] += 1
        chat.chat_write(file, history[-1:], delim=args.delim, invitation=args.delim)

        count += 1
    return count


async def run_agent(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None):
    """Run an agent."""
    function = agent["fn"]
    logger.debug("query: %r", query)
    return await function(agent, query, file, args, history, history_start=history_start, mission=mission, summary=summary, config=config, agents=agents)


async def local_agent(agent, _query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None):
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
    context = chat.context_remove_thinking_sections(context, agent["name"])

    # missions
    include_mission = agent.get("type") != "image_a1111"  # TODO clean this

    image_agent = agent.get("type", "").startswith("image_")
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
    if system_bottom:
        n_messages = len(context)
        pos = agent.get("system_bottom_pos", 0)
        pos = min(pos, n_messages)
        system_bottom_role = agent.get("system_bottom_role", "System")
        if system_bottom_role:
            context.insert(n_messages - pos, f"{system_bottom_role}:\t{system_bottom}")
        else:
            context.insert(n_messages - pos, f"{system_bottom}")
        logger.info("system_bottom: %r", system_bottom)
    if system_top:
        system_top_role = agent.get("system_top_role", None)
        context.insert(0, f"{system_top_role}:\t{system_top}")
        logger.info("system_top: %r", system_top)

    logger.debug("context: %s", args.delim.join(context[-6:]))

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

        logger.debug("clean_image_prompt: after: %s", text)
        return text

    clean_prompt = agent.get("clean_prompt", False)
    if clean_prompt:
        fulltext = clean_image_prompt(context, agent_name_esc)
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
        logger.info("fulltext after adding configured image prompts: %r", fulltext2)
    else:
        fulltext2 = fulltext

    service = agent["type"]

    portal = portals.get_portal(service)

    logger.debug("fulltext: %r", fulltext2)
    logger.debug("config: %r", gen_config)
    logger.debug("portal: %r", str(portal.portal))

    response, resp = await client_request(portal, fulltext2, config=gen_config, timeout=LOCAL_AGENT_TIMEOUT)

    apply_maps(agent["output_map"], agent["output_map_cs"], [response])

    room = chat.Room(path=Path(file))

    # try to get image seed from response
    seed = None
    try:
        # read result.yaml
        data = yaml.safe_load((resp / "result.yaml").read_text(encoding="utf-8"))
        seed = data["seed"]
    except (FileNotFoundError, KeyError):
        pass

    # look for attachments, other files in resp/ in sorted order
    # service image_a1111 should return a file name in response
    for resp_file in sorted(resp.iterdir()):
        if resp_file.name in ["new.txt", "request.txt", "config.yaml", "log.txt", "result.yaml"]:
            continue
        if seed and Path(resp_file).suffix in [".png", ".jpg"]:
            text = f"#{seed} {fulltext}"
            seed += 1
        else:
            text = fulltext
        name, _url, _medium, markdown, task = await chat.upload_file(room.name, agent["name"], str(resp_file), alt=text)
        if task:
            add_task(task, f"upload post-processing: {name}")
        if response:
            response += " "
        else:
            response += "\n"
        response += markdown

    await portal.remove_response(resp)

    logger.debug("response: %r", response)

    agent_names = list(agents.keys())
    history_messages = list(chat.lines_to_messages(history))
    all_people = conductor.participants(history_messages)
    people_lc = list(map(str.lower, set(agent_names + all_people)))

    response = trim_response(response, args, agent["name"], people_lc=people_lc)
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
    for config in configs:
        if "image_prompt_map" in config:
            for k, v in config["image_prompt_map"].items():
                positive = re.sub(str(k), str(v), positive)
        if "image_prompt_negative_map" in config:
            for k, v in config["image_prompt_negative_map"].items():
                negative = re.sub(str(k), str(v), negative)
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


async def remote_agent(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None):
    """Run a remote agent."""
    service = agent["type"]

    n_context = agent["default_context"]
    context = history[-n_context:]
    # XXX history is a list of lines, not messages, so won't the context sometimes contain partial messages? Yuk. That will interact badly with missions, too.
    # hacky temporary fix here for now, seems to work:
    while context and context[0].startswith("\t"):
        logger.debug("removing partial message at start of context: %r", context[0])
        context.pop(0)

    # remove "thinking" sections from context
    context = chat.context_remove_thinking_sections(context, agent["name"])

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
    system_bottom_role = "user" if service == "google" else agent.get("system_bottom_role", "user")
    system_top_role = "user" if service == "google" else agent.get("system_top_role", "system")
    if system_bottom:
        n_messages = len(remote_messages)
        pos = agent.get("system_bottom_pos", 0)
        pos = min(pos, n_messages)
        remote_messages.insert(n_messages - pos, {"role": system_bottom_role, "content": system_bottom})
    if system_top:
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
    response = fix_layout(response, args, agent)
    logger.debug("response 2: %r", response)
    response = f'{agent["name"]}:\t{response.strip()}'
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


async def safe_shell(agent, query, file, args, history, history_start=0, command=None, mission=None, summary=None, config=None, agents=None):
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
    cmd_str = ". ~/.profile ; "
    cmd_str += " ".join(map(shlex.quote, agent["command"]))

    command = ["sshc", "allemande-nobody@localhost", "bash", "-c", cmd_str]

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
    response3 = fix_layout(response2, args, agent)
    logger.debug("response3:\n%s", response3)
    return response3


async def file_changed(file_path, change_type, old_size, new_size, args, skip, agents):
    """Process a file change."""
    if args.ext and not file_path.endswith(args.ext):
        return
    if change_type == Change.deleted:
        return
    if not args.shrink and old_size and new_size < old_size:
        return
    if old_size is None and new_size == 0:
        return
    #     if new_size == 0 and old_size != 0:
    #         return

    if skip.get(file_path):
        logger.debug("Won't react to AI response: %r", file_path)
        skip[file_path] -= 1
        return

    try:
        logger.info("Processing file: %r", file_path)
        count = await process_file(file_path, args, skip=skip, agents=agents)
        logger.info("Processed file: %r, %r agents responded", file_path, count)
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


def write_agents_list(agents):
    """Write the list of agents to a file."""
    agent_names = list(agents.keys())
    path = PATH_ROOMS / "agents.yml"
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(agent_names, f)


def agent_get_all_names(agent: Agent) -> list[str]:
    """Get all the names for an agent."""
    agent_names = [agent["name"]]
    fullname = agent.get("fullname")
    if fullname:
        agent_names.append(fullname)
        if " " in fullname:
            agent_names.append(fullname.split(" ")[0])
    agent_names.extend(agent.get("aliases", []))
    return agent_names


def load_agent(agents, agent_file):
    """Load an agent from a file."""
    name = Path(agent_file).stem
    remove_agent(agents, name)

    with open(agent_file, encoding="utf-8") as f:
        agent = yaml.safe_load(f)

    if "name" not in agent:
        agent["name"] = name
    elif agent["name"].lower() != name.lower():
        raise ValueError(f'Agent name mismatch: {name} vs {agent["name"]}')

    update_visual(agent)

    agent = set_up_agent(agent)

    if not agent:
        return

    all_names = agent_get_all_names(agent)

    for name_lc in map(str.lower, all_names):
        if name_lc in agents:
            if agents[name_lc] != agent:
                old_main_name = agents[name_lc]["name"]
                logger.warning("Agent name conflict: %r vs %r for %r", old_main_name, agent["name"], name_lc)
            continue
        agents[name_lc] = agent

    return agent


def update_visual(agent: Agent):
    """Update the visual prompts for an agent."""
    visual = agent.get("visual")
    if not visual:
        return
    name = agent["name"].lower()
    name_lc = name.lower()
    all_names = agent_get_all_names(agent)

    for key in "person", "person/clothes":
        if key not in visual:
            continue
        prompt = visual.get(key)
        if prompt:
            prompt = prompt.strip() + "\n"
            (PATH_VISUAL/key).mkdir(parents=True, exist_ok=True)
            cache.save(str(PATH_VISUAL / key / name_lc) + ".txt", prompt, noclobber=False)
            # symlink the main file to the agent's other names
            for name in all_names:
                for dest in name, name.lower():
                    if dest == name_lc:
                        continue
                    cache.symlink(name_lc + ".txt", str(PATH_VISUAL / key / dest) + ".txt")

def remove_visual(agent: Agent):
    """Remove the visual prompts for an agent."""
    name = agent["name"].lower()
    name_lc = name.lower()
    all_names = agent_get_all_names(agent)

    for key in "person", "person/clothes":
        for name in all_names:
            for dest in name, name.lower():
                try:
                    os.remove(str(PATH_VISUAL / key / dest) + ".txt")
                except FileNotFoundError:
                    pass


def remove_agent(agents: dict[str, Agent], name: str):
    """Remove an agent."""
    agent = agents.get(name.lower())
    if not agent:
        return
    agent_names = agent_get_all_names(agent)
    for name_lc in map(str.lower, agent_names):
        agents.pop(name_lc, None)

    remove_visual(agent)


def load_agents(base_dir=None, agents=None):
    """Load all agents"""
    if not agents:
        agents = {}
    if not base_dir:
        base_dir = PATH_AGENTS

    for agent_file in base_dir.glob("*.yml"):
        try:
            load_agent(agents, agent_file)
        except Exception:  # pylint: disable=broad-except
            logger.exception("Error loading agent", exc_info=True)

    write_agents_list(agents)

    return agents


def agent_file_changed(agents: dict, file_path: str, change_type: Change):
    """Process an agent file change."""
    if change_type == Change.deleted:
        name = Path(file_path).stem
        logger.info("Removing agent: %r", name)
        remove_agent(agents, name)
    else:
        logger.info("Loading agent: %r", file_path)
        load_agent(agents, file_path)


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

    agents = load_agents()

    async with atail.AsyncTail(filename=args.watch, follow=True, rewind=True) as queue:
        while (line := await queue.get()) is not None:
            list_active_tasks()

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
                elif file_type == "agent":
                    agent_file_changed(agents, file_path, change_type)
                    write_agents_list(agents)
                else:
                    logger.info("Ignoring change to file: %r", file_path)
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
    for mod in sys.modules.values():
        file = getattr(mod, "__file__", None)
        if file and file.startswith(str(PATH_HOME)) and not "/venv/" in file and file.endswith(".py"):
            code_files.append(mod.__file__)

    return code_files


async def restart_if_code_changes():
    """Watch for code changes and restart the service."""
    code_files = get_code_files()

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
    logger.info("model_path: %r", model_path)
    if args.model and model_path.exists():
        # This will block, but it doesn't matter because this is the init for the program.
        return load_tokenizer(model_path)
    return None


services = {
    "llm_llama":    {"type": "portal", "fn": local_agent},
    "image_a1111":  {"type": "portal", "fn": local_agent},
    "openai":       {"type": "remote", "fn": remote_agent},
    "anthropic":    {"type": "remote", "fn": remote_agent},
    "google":       {"type": "remote", "fn": remote_agent},
    "perplexity":   {"type": "remote", "fn": remote_agent},
    "safe_shell":   {"type": "tool", "fn": safe_shell, "safe": False},  # ironically
    "search":       {"type": "tool", "fn": run_search},
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

    logger.info("Watching")
    asyncio.create_task(restart_if_code_changes())
    await watch_loop(args)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("interrupted")
        sys.exit(0)
