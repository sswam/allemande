""" Ally Chat: Local agent interface. """

import os
import logging
import re
from pathlib import Path
import yaml

import regex
from num2words import num2words  # type: ignore

import conductor
import chat
import bb_lib
import ally_markdown
from settings import LOCAL_AGENT_TIMEOUT, PATH_MODELS
from ally import portals  # type: ignore, pylint: disable=wrong-import-order
from ally_room import Room
import tasks

os.environ["TRANSFORMERS_OFFLINE"] = "1"
import transformers  # type: ignore # pylint: disable=wrong-import-position, wrong-import-order


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKENIZERS: dict[str, transformers.AutoTokenizer] = {}


def load_tokenizer(model_path: Path):
    """Load the Llama tokenizer"""
    return transformers.AutoTokenizer.from_pretrained(str(model_path))


def count_tokens_in_text(text, tokenizer):
    """Count the number of tokens in a text."""
    return len(tokenizer(text).input_ids)


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


def init(args):
    """Initialize the local agent interface."""
    TOKENIZERS[args.model] = load_model_tokenizer(args)


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


def get_fulltext(args, model_name, history, history_start, invitation, delim):
    """Get the full text from the history, and cut to the right length for a local model."""
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


def code_unwrap_input(message: str) -> str:
    """Remove ``` code quoting from a message"""
    message = re.sub(r'```[\w]*\n?', '', message)
    return message


def strip_images(message: str) -> str:
    """Remove images from a message, e.g. ![image](image.jpg)"""
    message = re.sub(r'!\[[^\]]*\]\([^\)]+\)', '', message)
    return message


async def local_agent(agent, _query, file, args, history, history_start=0, mission=None, summary=None, config=None, agents=None, responsible_human: str = None) -> str:
    """Run a local agent."""
    # print("local_agent: %r %r %r %r %r %r", query, agent, file, args, history, history_start)

    room = Room(path=Path(file))

    if config is None:
        config = {}

    # Note: the invitation should not end with a space, or the model might use lots of emojis!
    name = agent.name

    # Allow to override agent settings in the config
    agent = agent.copy()
    if config and config.get("agents") and "all" in config["agents"]:
        agent.update(config["agents"]["all"])
    if config and config.get("agents") and name in config["agents"]:
        agent.update(config["agents"][name])

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
    context = chat.context_remove_image_details(context)

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
        context = context2

    # add system messages
    system_top = agent.get("system_top", room=room.name)
    system_bottom = agent.get("system_bottom", room=room.name)

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
        if system_top_role:
            context.insert(0, f"{system_top_role}:\t{system_top}")
        else:
            context.insert(0, system_top)
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
        if agent.get("code_unwrap_input"):
            context = [code_unwrap_input(line) for line in context]
        if agent.get("strip_images_input"):
            context = [strip_images(line) for line in context]
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

    if "temp" in agent:
        gen_config["temperature"] = agent["temp"]

    # TODO: These stop regexps don't yet handle names with spaces or punctuation.

    #    r"(?umi)^(?!" + agent_name_esc + r"\s*:)[\p{L}][\p{L}\p{N}_]*:\s*\Z",

    if not image_agent:
        gen_config["stop_regexs"] = []
    if not image_agent and not agent.get("allow_play_script"):
        gen_config["stop_regexs"] += [
            # First pattern: Match one or two-word capitalized names at line start
            r'''(?umx)                 # Enable unicode, multiline, verbose mode
                ^                      # Start of line
                \s*                    # Optional whitespace
                (?!                    # Negative lookahead
                    ''' + agent_name_esc + r'''   # Don't match agent's name
                    \s*:               # Followed by optional whitespace and colon
                )
                [\p{Lu}]               # First word starts with uppercase
                [\p{L}\p{N}_]*         # Rest of first word
                (                      # Optional second word
                    \s                 # Space between words
                    [\p{Lu}]           # Second word starts with uppercase
                    [\p{L}\p{N}_]*     # Rest of second word
                )?                     # Optional second word
                :                      # Colon
                \s                     # Whitespace
            '''

            # # Second pattern: Match capitalized names with tab (except agent's name) anywhere in the line
            # Disabled for now, hopefully isn't needed
            # r'''(?ux)                 # Enable unicode and verbose mode
            #     \b                     # Word boundary
            #     (?!                    # Negative lookahead
            #         ''' + agent_name_esc + r''':  # Don't match agent's name and colon
            #     )
            #     [\p{Lu}]               # Must start with uppercase letter
            #     [\p{L}\p{N}_]*         # Rest of name: letters, numbers, underscore
            #     :                      # Colon
            #     \t                     # Tab character
            # ''',
        ]
    if not image_agent:
        # If no history, stop after the first line always. It tends to run away otherwise.
        if not history or (len(history) == 1 and history[0].startswith("System:\t")):
            logger.debug("No history, will stop after the first line.")
            gen_config["stop_regexs"].append(r"\n")

        gen_config["stop_regexs"].extend(agent.get("stop_regexs", []))

    if image_agent:
        fulltext2 = chat.add_configured_image_prompts(fulltext, [agent, config])
        logger.debug("fulltext after adding configured image prompts: %r", fulltext2)
    else:
        fulltext2 = fulltext

    service = agent["type"]

#     logger.info("service: %r", service)

    portal = portals.get_portal(service)

    logger.debug("fulltext: %r", fulltext2)
    logger.debug("config: %r", gen_config)
#     logger.info("portal: %r", str(portal.portal))

    gen_config["user"] = responsible_human

    response, resp = await client_request(portal, fulltext2, config=gen_config, timeout=LOCAL_AGENT_TIMEOUT)

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
            tasks.add_task(task, f"upload post-processing: {name}")
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

    response = chat.trim_response(response, args, agent.name, people_lc=people_lc)
    response = chat.fix_response_layout(response, args, agent)

    if agent.get("code_wrap_output"):
        response = "```\n\t" + response.strip() + "\n\t```"

    if invitation:
        tidy_response = invitation.strip() + "\t" + response.strip()
    else:
        tidy_response = response

    # TODO accept attachments from model

    logger.debug("tidy response: %r", tidy_response)

    return tidy_response
