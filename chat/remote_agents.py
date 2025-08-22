""" Ally Chat: Remote agent interface. """

import logging
import re
import json
from pprint import pformat
from pathlib import Path

from num2words import num2words

import conductor
import tab  # type: ignore, pylint: disable=wrong-import-order
import chat
import bb_lib
import ally_markdown
import llm  # type: ignore, pylint: disable=wrong-import-order
from settings import REMOTE_AGENT_RETRIES
from ally_room import Room

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Placeholder content where the LLM expects a user message.
USER_PLACEHOLDER_CONTENT = "..."

async def remote_agent(agent, query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None, responsible_human: str = None) -> str:
    """Run a remote agent."""
    # NOTE: responsible_human is not used here yet

    room = Room(path=Path(file))

    service = agent["type"]

    if config is None:
        config = {}

    name = agent.name

    # Allow to override agent settings in the config
    agent = agent.copy()
    if config and config.get("agents") and "all" in config["agents"]:
        agent.update(config["agents"]["all"])
    if config and config.get("agents") and name in config["agents"]:
        agent.update(config["agents"][name])

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

    # # remove image details (alt text)
    # context = chat.context_remove_image_details(context)

    # prepend mission / info / context
    # TODO try mission as a "system" message?
    context2 = []
    mission_pos = config.get("mission_pos", 0)
    if summary:
        context2 += f"System:\t{summary}"
    context2 += context
    if mission:
        context2.insert(mission_pos, "System:\t" + "\n".join(mission))

    context_messages = list(bb_lib.lines_to_messages(context2))

    remote_messages = []

    # TODO images in system messages?
    await chat.add_images_to_messages(file, context_messages, agent.get("images", 0))

    # preprocess markdown in messages for includes
    for m in context_messages:
        m["content"] = (await ally_markdown.preprocess(m["content"], file, m.get("user")))[0]

    # TODO Can't include from system messages, what user permission to use?

    # convert context_messages to remote_messages, with only user and assistant roles

    for msg in context_messages:
        logger.debug("msg1: %r", msg)
        u = msg.get("user") or ""
        content = msg["content"]
        if u == agent.name:
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

    # Google Gemini doesn't like NSFW images in the most recent message?! but cool otherwise!
    if agent.get("blank_message_after_image") and remote_messages and "images" in remote_messages[-1]:
        remote_messages.append({"role":"assistant", "content":""})

    # Google Gemini doesn't like the first message to be an assistant message, so we add a user message if needed
    if remote_messages and remote_messages[0]["role"] == "assistant" and agent["type"] in ["anthropic", "google"]:
        remote_messages.insert(0, {"role": "user", "content": USER_PLACEHOLDER_CONTENT})

    # add system messages
    system_top = agent.get("system_top", room=room.name)
    system_bottom = agent.get("system_bottom", room=room.name)
    system_bottom_role = "user" if service == "google" else agent.get("system_bottom_role", "user")
    system_top_role = agent.get("system_top_role", "system")

    # add system message for age
    age_input = agent.get("age")
    age = None
    if isinstance(age_input, str):
        age = age_input
    elif age_input:  # If it's a number
        age = num2words(age_input) + " years old"
    if age and system_top:
        system_top += f"\n\n(You are {age}.)"
    elif age and system_bottom:
        system_bottom += f"\n\n(You are {age}.)"
    elif age:
        logger.warning("age provided but no system message to add it to, for agent %r", agent.name)

    # add system message for self_image
    self_image = agent.get("self_image")
    if self_image and system_top:
        system_top += "\n\n" + self_image
    elif self_image and system_bottom:
        system_bottom += "\n\n" + self_image
    elif self_image:
        logger.warning("self_image provided but no system message to add it to, for agent %r", agent.name)

    logger.debug("system message for %s: %s", agent.name, system_top or system_bottom)

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

    if "config" not in agent:
        agent["config"] = {}
    if "temp" in agent:
        agent["config"]["temperature"] = agent["temp"]

    opts = llm.Options(model=agent["model"])  # , indent="\t")
    for k, v in agent.get("config", {}).items():
        setattr(opts, k, v)
    if agent.get("vision") is False:
        opts.vision = False

    logger.debug("config: %r", config)
    logger.debug("agent: %r", agent.data)

    # Some agents don't like empty content, specifically google
    if not remote_messages[-1]["content"]:
        remote_messages[-1]["content"] = USER_PLACEHOLDER_CONTENT
    remote_messages = [m for m in remote_messages if m["content"]]

    # Set up stop sequences for other participants
    logger.debug("context_messages: %r", context_messages)
    all_people = conductor.get_all_participants(context_messages)
    if opts.stop is None:
        opts.stop = []
    if opts.stop is not False:
        for p in all_people:
            if p == agent.name:
                continue
            opts.stop.append(f"\n\n{p}: ")

    logger.debug("stop: %r", opts.stop)

    logger.debug("remote_messages: %s", pformat(remote_messages))
    logger.debug("remote_messages: %s", json.dumps(remote_messages, indent=2))

    ###### the actual query ######
    logger.debug("querying %r = %r", agent.name, agent["model"])
    try:
        output_message = await llm.aretry(llm.allm_chat, REMOTE_AGENT_RETRIES, opts, remote_messages)
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("Exception during generation")
        msg = str(e)
        if msg in ["list index out of range"]:
            msg = ""
        return f"{agent.name}:\n" + re.sub(r'(?m)^', '\t', msg)
    #google.generativeai.types.generation_types.StopCandidateException: finish_reason: PROHIBITED_CONTENT

    response = output_message["content"]

    if response is None:
        response = ""

    if response.startswith(agent.name + ": "):
        logger.debug("stripping agent name from response")
        response = response[len(agent.name) + 2 :]

    # fix indentation for code
    if opts.indent:
        lines = response.splitlines()
        lines = tab.fix_indentation_list(lines, opts.indent)
        response = "".join(lines)

    logger.debug("response 1: %r", response)
    response = chat.fix_response_layout(response, args, agent)
    logger.debug("response 2: %r", response)
    response = f'{agent.name}:\t{response.strip()}'
    logger.debug("response 3: %r", response)
    return response.rstrip()
