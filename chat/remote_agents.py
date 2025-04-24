""" Ally Chat: Remote agent interface. """

import logging
import re
import json
from pprint import pformat

from num2words import num2words

import conductor
import tab  # type: ignore, pylint: disable=wrong-import-order
import chat
import bb_lib
import ally_markdown
import llm  # type: ignore, pylint: disable=wrong-import-order
from settings import REMOTE_AGENT_RETRIES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    chat.apply_maps(agent["input_map"], agent["input_map_cs"], context2)

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
    chat.apply_maps(agent["output_map"], agent["output_map_cs"], box)
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
    response = chat.fix_response_layout(response, args, agent)
    logger.debug("response 2: %r", response)
    response = f'{agent.name}:\t{response.strip()}'
    logger.debug("response 3: %r", response)
    return response.rstrip()
