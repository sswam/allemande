#!/usr/bin/env python3-allemande

""" Allemande chat library """

import os
import sys
import html
from pathlib import Path
import re
import logging
from typing import Any, Callable
import shutil
import random
import asyncio
import copy

import regex
import argh
import aiofiles
from bs4 import BeautifulSoup

from util import sanitize_filename
from ally.cache import cache  # type: ignore
from bb_lib import ChatMessage, save_chat_messages, load_chat_messages
import video_compatible  # type: ignore  # pylint: disable=wrong-import-order
import aligno_py as aligno  # type: ignore
from ally import re_map


Message = dict[str, Any]   # TODO use a class, bb_lib.ChatMessage?


# os.umask(0o027)
os.umask(0o002)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


Agent = dict[str, Any]


def chat_read(file, _args) -> list[str]:
    """Read the chat history from a file."""
    # TODO what was args for?
    text = ""
    if file and os.path.exists(file):
        with open(file, encoding="utf-8") as f:
            text = f.read()
    # lookahead for non-space after newline
    history = re.split(r"\n+(?=\S|$)", text) if text else []

    if history and not history[-1]:
        history.pop()
    return history


def chat_write(file, history, delim="\n", mode="a", invitation=""):
    """Write or append the chat history to a file."""
    if not file:
        return
    text = delim.join(history) + invitation
    with open(file, mode, encoding="utf-8") as f:
        f.write(text)


def process_chat(messages: list[ChatMessage], process_fn: Callable) -> list[ChatMessage]:
    """Process chat messages using the provided function.

    Args:
        messages: List of ChatMessage objects to process
        process_fn: Function that takes a ChatMessage and returns a processed ChatMessage or None

    Returns:
        List of processed ChatMessage objects, excluding any that were filtered out
    """
    processed_messages = []

    for msg in messages:
        result = process_fn(msg)
        if result is not None:
            processed_messages.append(result)

    return processed_messages


def filter_stars(message: ChatMessage) -> ChatMessage | None:
    """
    Process a message by:
    1. Removing text between * and * (shortest matches) including delimiters
    2. Removing lines that begin or end with *
    3. Testing if remainder is just whitespace - if so, skip message

    Args:
        message: ChatMessage to process

    Returns:
        Original message if content remains after filtering, None if only whitespace remains
    """
    # Make a working copy of the content
    content = message.content

    # 1. Remove text between * and * (non-greedy match)
    content = re.sub(r"\*.*?\*", "", content)

    # 2. Remove lines that begin or end with *
    lines = content.split("\n")
    lines = [line for line in lines if not (line.strip().startswith("*") or line.strip().endswith("*"))]
    content = "\n".join(lines)

    # 3. Check if only whitespace remains
    if not content.strip():
        return None

    # If we get here, there's non-whitespace content, so return original message
    return message


def filter_stars_prob(message: ChatMessage, prob: float = 0.5) -> ChatMessage | None:
    """
    Remove a certain proportion of stars / emotions / actions text from the message.
    If nothing is left, return None.

    Args:
        message: ChatMessage to process
        prob: Probability (0.0 to 1.0) of applying the filter to each starred section

    Returns:
        Processed message or None if only whitespace remains
    """
    if prob <= 0.0:
        return message

    # Make a working copy of the content
    content = message.content

    # 1. Fix malformed lines that begin or end with * but not both, by adding the missing *
    lines = content.split("\n")
    lines_out = []
    for line in lines:
        if line.strip().startswith("*") and not line.strip().endswith("*"):
            line += "*"
        if line.strip().endswith("*") and not line.strip().startswith("*"):
            line = "*" + line
        lines_out.append(line)
    content = "\n".join(lines_out)

    # 2. Remove random selection of text between * and * (non-greedy match)
    def random_replace(match):
        """Replace match with empty string with probability prob."""
        return "" if random.random() < prob else match.group(0)

    content = re.sub(r"\*.*?\*", random_replace, content)

    # 3. squeeze whitespace and strip, preserving the format
    content = re.sub(r"\s*\n\n+\s*", "\n\n", content)
    content = re.sub(r" +", " ", content)
    content = content.strip()

    # 4. Check if anything remains
    if not content:
        return None

    # Create new message with filtered content
    return ChatMessage(
        user=message.user,
        content=content,
    )


def remove_thinking_sections(content: str, agent: Agent | None, n_own_messages: int) -> tuple[str, int]:
    """Remove "thinking" sections from the content."""
    remember_thoughts = agent.get("remember_thoughts", 0) if agent else 0
    if agent:
        logger.debug("Agent name %s, remember_thoughts %s, n_own_messages %s", agent["name"], remember_thoughts, n_own_messages)
    agent_name = agent["name"] if agent else None
    replace = ""
    if agent_name and content.startswith(agent_name + ":\t"):
        n_own_messages += 1
        if n_own_messages <= remember_thoughts:
            logger.debug("Remembering agent's thoughts: %s", content)
            return content, n_own_messages
        #        replace = "<think>\nI was thinking something ...\n</think>"
        replace = ""
    modified = re.sub(
        r"""
        <think(ing)?>
        (.*?)
        (</think(ing)?>|\Z)
        """,
        replace,
        content,
        flags=re.MULTILINE | re.IGNORECASE | re.VERBOSE | re.DOTALL,
    )
    if modified != content:
        logger.debug("Removed 'thinking' section/s from message: original: %s", content)
        logger.debug("  modified: %s", modified)
        return modified, n_own_messages
    logger.debug("No 'thinking' section/s found in message: %s", content)
    return content, n_own_messages


def context_remove_thinking_sections(context: list[str], agent: Agent | None) -> list[str]:
    """Remove "thinking" sections from the context."""
    # Remove any "thinking" sections from the context
    # A "thinking" section is a <think> block

    n = len(context)
    n_own_messages = 0
    for i in range(n - 1, -1, -1):
        context[i], n_own_messages = remove_thinking_sections(context[i], agent, n_own_messages)

    return context


def remove_image_details(content: str) -> str:
    """Remove image details from the content."""
    modified = re.sub(r"!\[(#\d+) (.*?)\]\((.*?)\)", r"![](\3)", content)
    if modified != content:
        logger.debug("Removed image details from message: original: %s", content)
        logger.debug("  modified: %s", modified)
    return modified


def context_remove_image_details(context: list[str]) -> list[str]:
    """Remove image details from the context."""

    n = len(context)
    for i in range(n - 1, -1, -1):
        context[i] = remove_image_details(context[i])

    return context


def history_remove_thinking_sections(history: list[dict[str, Any]], agent: Agent | None):
    """Remove "thinking" sections from the history."""
    # Remove any "thinking" sections from the context
    # A "thinking" section is a <think> block

    history = copy.deepcopy(history)

    n = len(history)
    n_own_messages = 0
    for i in range(n - 1, -1, -1):
        message = history[i]
        message["content"], n_own_messages = remove_thinking_sections(message["content"], agent, n_own_messages)

    return history


process_fn = None


def process_chat_cli(code: str | None = None, func: str | None = None):
    """Read a chat file from stdin, process it with a Python expression from the CLI, and write the result to stdout."""
    messages = load_chat_messages()
    if func:
        globals()["process_fn"] = globals()[func]
    elif code is not None:
        code = code.replace("\n", "\n    ")
        code = f"""
import re
def process_fn(msg):
    u = msg.user
    c = msg.content
    {code}
    if not c:
        return None
    return ChatMessage(u, c)
"""
        exec(code, globals())  # pylint: disable=exec-used

    if process_fn is None:
        raise ValueError("No function or code provided for processing.")

    processed_messages = process_chat(messages, process_fn)
    save_chat_messages(processed_messages)


def clean_prompt(context, name, delim):
    """Clean the prompt for image gen agents and tools."""
    # No longer needed, replaced with trivial version for now.
    return "".join(context)


def set_user_theme(user, theme):
    """Set the user's theme."""
    if sanitize_filename(theme) != theme:
        raise ValueError("Invalid theme name.")
    path = Path(os.environ["ALLEMANDE_USERS"]) / user / "theme.css"
    source = "../../themes/" + theme + ".css"
    if not (Path(os.environ["ALLEMANDE_USERS"]) / user / source).exists:
        raise ValueError("Theme not found.")
    path.parent.mkdir(parents=True, exist_ok=True)
    cache.chmod(path.parent, 0o755)
    cache.symlink(source, path)


# pylint: disable=too-many-branches
def apply_editing_commands(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Apply editing commands to the chat history."""
    #     logger.info("\n\n\n")
    #     logger.info("messages before editing commands: %r", messages)
    #     logger.info("\n\n\n")
    lookup = messages.copy()
    for i, message in enumerate(messages):
        m = re.search(r"""(<ac\b[-a-z0-9 ="']*>)\s*$""", message["content"], flags=re.IGNORECASE)
        if not m:
            continue
        xmltext = m.group(1).strip()
        # chop it off the message content
        message["content"] = message["content"][: m.start()].rstrip()
        soup = BeautifulSoup(xmltext, "html.parser")
        meta = soup.find("ac")
        if not meta:
            raise ValueError("Invalid ac tag.")

        remove = meta.get("rm")
        edit = meta.get("edit")
        insert = meta.get("insert")

        # handle erroneous content, should be only digits and spaces
        if not re.match(r"[0-9 ]+$", remove or ""):
            logger.warning("Invalid remove attribute in message %s: %s", i, remove)
            remove = None

        # remove the rm, edit and insert attributes
        for attr in ["rm", "edit", "insert"]:
            if attr in meta.attrs:
                del meta[attr]
        # add the meta tag back to the message content if there are any remaining attributes
        if meta.attrs:
            message["content"] += str(meta)

        rm_ids = []
        if edit:
            rm_ids.append(int(edit))
        elif remove:
            rm_ids += list(map(int, remove.split(" ")))
        for rm_id in rm_ids:
            if rm_id < len(lookup):
                #                 logger.warning("Removing message ID: %s", rm_id)
                lookup[rm_id]["rm"] = True
            else:
                logger.warning("Invalid message ID in editing command: %s", rm_id)

        if edit and insert:
            logger.warning("Both edit and insert attributes in the same message, will edit: %s", message)

        target = edit or insert
        if target is not None:
            if "before" not in lookup[int(target)]:
                lookup[int(target)]["before"] = [message]
            else:
                lookup[int(target)]["before"].append(message)
            messages[i] = None

        #         logger.info("message ID: %s, remove: %s, edit: %s, insert: %s, content: %s", i, remove, edit, insert, message["content"])

        # if a message that wasn't moved is now empty, mark it for removal
        if remove and not edit and not insert and not message["content"].strip():
            #             logger.warning("Removing editing message ID: %s", i)
            messages[i]["rm"] = True

    #     logger.info("messages after editing commands: %r", messages)
    #     logger.info("\n\n\n")

    output: list[dict[str, Any]] = []
    flatten_edited_messages(messages, output)

    #     logger.info("apply_editing_commands: output: %r", output)
    #     logger.info("\n\n\n")

    return output


def flatten_edited_messages(messages, output):
    """Flatten edited messages."""
    for message in messages:
        if message is None:
            continue
        if "before" in message:
            flatten_edited_messages(message["before"], output)
        if "rm" not in message:
            output.append(message)


def fix_response_layout(response, agent):
    """Fix the layout and indentation of the response."""
    logger.debug("response before fix_layout: %s", response)
    lines = re.split(r"\n|\r\n|\r", response)
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

    # TODO ideally don't apply this to code blocks
    if agent.get("dedent"):
        lines = [line.strip() for line in lines]

    # Remove agent's name, if present
    logger.debug("lines[0]: %r", lines[0])
    logger.debug("agent.name: %r", agent.name)
    name_part = None

    name_pattern = r'^(\*|_|\*\*|__)?' + re.escape(agent.name) + r'(?::\1|\1:)\s(.*)'

    match = re.match(name_pattern, lines[0])
    if match:
        lines[0] = match.group(2)

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
        if not in_table and not in_code and ("---" in line or re.search(r"\|.*\|", line)):
            if i > 0 and lines[i - 1].strip():
                out.append("")
            in_table = True

        if in_table and not line.strip():
            in_table = False

        # detect if in_code
        if not in_table and not in_code and (re.search(r"```", line) or re.search(r"<script\b", line)):
            in_code = True
        elif in_code and (re.search(r"```", line) or re.search(r"</script>", line)):
            in_code = False

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


# def leading_spaces(text):
#     """Return the number of leading spaces in a text."""
#     return re.match(r"\s*", text).group(0)


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


def trim_response(response, args, agent_name, people_lc=None):
    """Trim the response to the first message."""
    logger.debug("trim_response: %r, %r, %r, %r", response, args, agent_name, people_lc)

    if people_lc is None:
        people_lc = []

    def check_person_remove(match):
        """Remove text starting with a known person's name."""
        # Get the full line of text after the newline
        full_line = match.group(1)
        logger.debug(f"Full line from match: '{full_line}'")

        # Extract the name part before the colon
        name_part = re.match(r"[ \t]*([^:]+)[ \t]*:", full_line)
        logger.debug(f"Extracted name_part: {name_part}")

        if name_part:
            extracted_name = name_part.group(1).lower().strip()
            logger.debug(f"Cleaned name: '{extracted_name}'")
            logger.debug(f"Known people (lowercase): {people_lc}")

            if extracted_name in people_lc:
                logger.debug(f"Name '{extracted_name}' found in people list - removing line")
                return ""
            else:
                logger.debug(f"Name '{extracted_name}' not found in people list - keeping line")
        else:
            logger.debug("No name pattern found in line")

        return match.group(1)

    response = response.strip()

    response_before = response

    # remove agent's own `name: ` from response
    agent_name_esc = re.escape(agent_name)
    response = re.sub(r"^[ \t]*" + agent_name_esc + r"[ \t]*:[ \t]*(.*)", r"\1", response, flags=re.MULTILINE)

    # remove anything after a known person's name
    response = re.sub(r"(\n[ \t]*[^:\n]+[ \t]*:[ \t]*.*)", check_person_remove, response, flags=re.DOTALL)

    if response != response_before:
        logger.debug("Trimmed response: %r\nto: %r", response_before, response)

    response = " " + response.strip()
    return response


def has_at_mention(content: str) -> bool:
    """Check if a message contains an @name mention"""
    return re.search(r'(\W|^)@\w', content)


def main():
    """Main function to run the CLI commands."""
    def proc(code: str | None = None, func: str | None = None):
        return process_chat_cli(code, func)

    argh.dispatch_commands(
        [
            proc,
        ]
    )


if __name__ == "__main__":
    main()
