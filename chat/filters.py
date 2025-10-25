"""
This module provides filters for processing chat responses and agent installations.
"""

import os
import random
import re
from pathlib import Path

import regex

from ally import logs  # type: ignore
import ally_agents  # type: ignore
import settings  # type: ignore
import util  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


def filter_out_agents_install(response: str) -> str:
    """Install agents from a response by extracting YAML blocks and saving them to files."""
    logger.debug("filter_out_agents_install input response:\n\n%s", response)

    # remove indent and role label
    dedented_response = re.sub(r"^.*?\t", "", response, flags=re.MULTILINE)

    # Extract YAML blocks
    yaml_blocks = regex.findall(
        r"```yaml\n(.*?)```",
        dedented_response,
        flags=regex.DOTALL | regex.IGNORECASE
    )

    all_yaml = "".join(yaml_blocks)
    logger.debug("Found %d YAML blocks in response: %r", len(yaml_blocks), yaml_blocks)

    # Extract agent files
    yaml_agents = regex.findall(
        r"^#File:\s*([^\n]+?\.yml)\s*?\n(.*?)(?=^#File:|\Z)",
        all_yaml,
        flags=regex.DOTALL | regex.MULTILINE | regex.IGNORECASE
    )

    logger.debug("Found %d agent files in YAML blocks: %r", len(yaml_agents), [name for name, _ in yaml_agents])

    agents_path = settings.PATH_ROOMS / "agents"

    for path_name, content in yaml_agents:
        # Sanitize filename

        # Process path components
        path_parts = Path(path_name).parts
        if "agents" in path_parts:
            agents_index = path_parts.index("agents")
            safe_path_name = Path(*path_parts[agents_index + 1:])
        else:
            # If "agents" not found, use the original path
            safe_path_name = Path(path_name)

        # Usage:
        file_path = (agents_path / safe_path_name).resolve()

        if not util.path_contains(agents_path, file_path):
            logger.warning(f"Attempted to install agent outside agents folder: {file_path}")
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

    return response


def filter_in_think_add_example(response: str, place: int, example: str = "I was thinking... what was I thinking...?") -> str:
    """Add an example <think> section to the response, if not already present."""
    # TODO make sure it's own message, not another agent's message
    # TODO maybe not needed?
    if place == 1 and "<think>" not in response:
        response = re.sub("\t", f"\t<think>{example}</think>\n\t", response, count=1)
    return response


def filter_in_think_brackets(response: str, place: int) -> str:
    """Replace <think>thinking sections</think> with [thinking sections]."""
    response = re.sub(r"<think>(.*?)</think>", lambda thought: f"[{thought.group(1).strip()}]", response, flags=re.DOTALL)
    return response


def filter_out_think_brackets(response: str) -> str:
    """Replace [thinking sections] with <think>thinking sections</think>."""
    # match at start and end of lines only, so we don't match images / links
    response = re.sub(r"\t\[(.*?)\]$", r"\t<think>\1</think>", response, flags=re.DOTALL|re.MULTILINE)
    return response


def filter_out_actions_reduce(response: str, keep_prob: float = 0.5) -> str:
    """Reduce the number of *actions* in the response, based on keep_prob (0-1)."""
    response2 = re.sub(r" *\*(.*?) (.*?)\*[.!?]* *",
        lambda action: action.group(0) if random.random() < keep_prob else " ",
        response, flags=re.DOTALL)

    # Strip spaces and reduce blank lines
    response2 = re.sub(r"^\t +", "\t", response2, flags=re.MULTILINE)
    response2 = re.sub(r" +$", "", response2, flags=re.MULTILINE)
    response2 = re.sub(r"\n{3,}", "\n\n", response2)

    if response2 and not re.search(r":\t?$", response2):
        return response2
    return response


RE_EMOJIS = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"  # dingbats
        u"\U000024C2-\U0001F251"  # enclosed characters
        u"\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
        u"\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-A
        u"\U00002600-\U000026FF"  # miscellaneous symbols
        u"\U00002B00-\U00002BFF"  # miscellaneous symbols and arrows
        u"\U0001F700-\U0001F77F"  # alchemical symbols
        u"\U0001F7E0-\U0001F7EB"  # geometric shapes extended
        u"\U0001F90C-\U0001F93A"  # additional emoticons
        u"\U0001F3FB-\U0001F3FF"  # skin tone modifiers
        "]+", flags=re.UNICODE)


def filter_out_emojis(response: str, keep_prob: float = 0.0) -> str:
    """Reduce the number of emojis in the response, based on keep_prob (0-1)."""
    if keep_prob == 0.0:
        return RE_EMOJIS.sub('', response)
    if keep_prob == 1.0:
        return response
    return RE_EMOJIS.sub(lambda m: m.group(0) if random.random() < keep_prob else '', response)


def filter_out_emdash(response: str, keep_prob: float = 0.0, replacement: str = "-") -> str:
    """Replace em-dash characters with a replacement string, based on keep_prob (0-1)."""
    # Handle different types of em-dashes and their Unicode variants
    emdash_pattern = r'( *)(?:[-\u2014\u2013\u2015] *?)+( *)' # includes em-dash, en-dash, and horizontal bar

    if keep_prob == 0.0:
        return re.sub(emdash_pattern, r"\1"+replacement+r"\2", response)
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
    if not filters:
        return query, history

    history_new = history.copy()

    for filter_name in filters:
        if isinstance(filter_name, list):
            filter_args = filter_name[1:]
            filter_name = filter_name[0]
        else:
            filter_args = []

        filter_fn = filters_in.get(filter_name)
        if not filter_fn:
            logger.warning("Agent %r: Unknown filter_in: %r", agent.name, filter_name)
            continue

        try:
            query = filter_fn(query, 0, *filter_args)
            hist_len = len(history_new)
            # NOTE: history[-1] is similar to query, but with the username prefix
            for i in range(hist_len):
                history_new[i] = filter_fn(history_new[i], hist_len - i, *filter_args)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Agent %r: Error in filter_in %r: %s", agent.name, filter_name, str(e))

    return query, history_new


def apply_filters_out(agent: ally_agents.Agent, response: str) -> str:
    """Apply output filters to the response."""
    filters = agent.get("filter_out")
    if not filters:
        return response

    for filter_name in filters:
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
