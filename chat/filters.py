"""
This module provides filters for processing chat responses and agent installations.
"""

import random
import re
from pathlib import Path

import regex

from ally import logs  # type: ignore
import ally_agents  # type: ignore
import settings  # type: ignore
import util  # type: ignore

__version__ = "0.1.3"

logger = logs.get_logger()


def filter_out_agents_install(response: str, root: str = "") -> str:
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

    root_path = settings.PATH_ROOMS / root

    for path_name, content in yaml_agents:
        # Sanitize filename

        # Process path components
        # path_parts = Path(path_name).parts
        # if "agents" in path_parts:
        #     agents_index = path_parts.index("agents")
        #     safe_path_name = Path(*path_parts[agents_index + 1:])
        # else:
        #     # If "agents" not found, use the original path
        #     safe_path_name = Path(path_name)
        safe_path_name = Path(path_name)


        file_path = (root_path / safe_path_name).resolve()

        if not util.path_contains(root_path, file_path):
            logger.warning(f"Attempted to install agent outside root folder: {file_path}")
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


def filter_out_think_fix(response: str) -> str:
    """Fix nesting and formatting of <think></think> containers."""
    logger.info("filter_think_fix 1 input: %s", response)

    # Extract all text between first <think> and last </think>
    think_pattern = r'<think>(.*)</think>'
    match = re.search(think_pattern, response, flags=re.DOTALL)

    if not match:
        logger.info("filter_think_fix 2: no think tags found")
        return response

    logger.info("filter_think_fix 2 found think tags: %s", match.group(0)[:100])

    # Get the content and position
    think_content = match.group(1)
    start_pos = match.start()
    end_pos = match.end()

    # Remove any nested <think> or </think> tags from content
    cleaned_content = re.sub(r'</?think>', '', think_content)
    logger.info("filter_think_fix 3 after removing nested tags: %s", cleaned_content[:100])

    # Get text before and after
    before = response[:start_pos]
    after = response[end_pos:]

    # Split before into lines to analyze the last line
    lines_before = before.split('\n')
    last_line = lines_before[-1] if lines_before else ''

    # Check if last line is just a label (e.g., "Acsi:" or "Assistant:")
    # A label is non-empty, doesn't end with newline, and is short
    is_label_line = bool(last_line.strip()) and not before.endswith('\n')

    if is_label_line:
        # Keep the label on same line with a tab before <think>
        before = before.rstrip()  # Remove any trailing whitespace
        result = f"{before}\t<think>\n\t{cleaned_content.strip()}\n\t</think>"
    else:
        # Standard case: put <think> on new line with proper indentation
        before = before.rstrip()

        # Determine indentation from context
        if lines_before and len(lines_before) > 1:
            # Look at previous lines for indentation pattern
            prev_line = lines_before[-2] if len(lines_before) > 1 else ''
            indent = '\t' if prev_line.startswith('\t') else '\t'
        else:
            indent = '\t'

        result = before
        if result and not result.endswith('\n'):
            result += '\n'
        result += f"{indent}<think>\n{indent}{cleaned_content.strip()}\n{indent}</think>"

    # Handle after content - ensure proper indentation
    if after:
        after = after.lstrip()  # Remove leading whitespace
        if after:
            # Split after content into lines and ensure each has proper indentation
            after_lines = after.split('\n')
            indented_lines = []
            for line in after_lines:
                stripped = line.lstrip()
                if stripped:  # Only add tab to non-empty lines
                    indented_lines.append('\t' + stripped)
                else:
                    indented_lines.append('')  # Preserve empty lines
            result += '\n' + '\n'.join(indented_lines)

    logger.info("filter_think_fix 4 output: %s", result)

    return result


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


def filter_out_fix_image_prompts(response: str) -> str:
    """Fix image prompts generated by ... less formal syntax-oriented agents!"""
    art_model_default = "Coni"

    logger.info("filter_out_fix_image_prompts 1: %s", response)

    # Strip leading tabs from all lines
    lines = response.split('\n')
    response = '\n'.join(line.lstrip('\t') for line in lines)

    # First pass: collect and fix properly quoted image prompts
    quoted_prompts = list(regex.finditer(r"```\s*(.*?)```", response, flags=regex.DOTALL))

    if quoted_prompts:
        logger.info("Found %d quoted image prompt blocks", len(quoted_prompts))
        response = fix_quoted_prompts(response, quoted_prompts, art_model_default)
    else:
        logger.info("No quoted image prompts found, checking for unquoted prompts")
        response = find_and_fix_unquoted_prompts(response, art_model_default)

    # Clean up $ArtModel lines outside of prompts
    response = remove_art_model_lines(response)

    # Remove chat: prefix from lines
    response = remove_chat_prefix(response)

    # Prefix each line other than the first with a leading tab
    lines = response.split('\n')
    if len(lines) > 1:
        response = lines[0] + '\n' + '\n'.join('\t' + line for line in lines[1:])

    return response


def fix_quoted_prompts(response: str, quoted_prompts: list, art_model_default: str) -> str:
    """Fix already-quoted image prompts in place."""
    offset = 0
    for match in quoted_prompts:
        prompt_content = match.group(1).strip()

        if not is_image_prompt(prompt_content):
            continue

        logger.info("Fixing quoted prompt: %s...", prompt_content[:50])
        fixed_content = fix_prompt_content(prompt_content, art_model_default)

        # Replace in response accounting for offset changes
        start = match.start() + offset
        end = match.end() + offset
        replacement = f"```\n{fixed_content}\n```"
        response = response[:start] + replacement + response[end:]
        offset += len(replacement) - (end - start)

    return response


def find_and_fix_unquoted_prompts(response: str, art_model_default: str) -> str:
    """Find unquoted image prompts and wrap them in code blocks."""
    lines = response.split('\n')
    result_lines: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if is_image_prompt(line):
            logger.info("Found unquoted image prompt at line %d", i)
            # Collect the whole paragraph
            prompt_lines = [line]
            j = i + 1
            while j < len(lines) and lines[j].strip() and is_image_prompt(lines[j]):
                prompt_lines.append(lines[j])
                j += 1

            # Fix and wrap the prompt
            prompt_content = '\n'.join(prompt_lines)
            fixed_content = fix_prompt_content(prompt_content, art_model_default)
            result_lines.append(f"```\n{fixed_content}\n```")

            i = j
            continue

        result_lines.append(line)
        i += 1

    return '\n'.join(result_lines)


def is_image_prompt(text: str) -> bool:
    """Check if text looks like an image prompt."""
    text = text.strip()

    if not text:
        return False

    # Check for various image prompt indicators
    if regex.match(r"^[A-Z]\w+,", text):
        return True

    if r"[person" in text:
        return True

    if r"[use" in text:
        return True

    if regex.search(r":\d", text):
        return True

    if "NEGATIVE" in text:
        return True

    if "BREAK" in text:
        return True

    return False


def fix_prompt_content(prompt: str, art_model_default: str) -> str:
    """Fix a single image prompt's content."""
    prompt = prompt.strip()

    # Remove $ArtModel prefix if present
    prompt = regex.sub(r"^\$ArtModel,?\s*", "", prompt, flags=regex.MULTILINE)

    # Check if it starts with an art model name
    if not regex.match(r"^[A-Z]\w+,", prompt):
        logger.info("Adding default art model '%s' to prompt", art_model_default)
        prompt = f"{art_model_default}, {prompt}"

    return prompt


def remove_art_model_lines(response: str) -> str:
    """Remove lines that begin with $ArtModel outside of code blocks."""
    lines = response.split('\n')
    result_lines: list[str] = []
    in_code_block = False

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            result_lines.append(line)
            continue

        if not in_code_block and regex.match(r"^\s*\$ArtModel\W", line):
            logger.info("Removing $ArtModel line: %s", line[:50])
            continue

        result_lines.append(line)

    return '\n'.join(result_lines)


def remove_chat_prefix(response: str) -> str:
    """Remove chat: prefix from lines."""
    lines = response.split('\n')
    result_lines: list[str] = []

    for line in lines:
        cleaned = regex.sub(r"^chat:\s*", "", line)
        if cleaned != line:
            logger.info("Removed 'chat:' prefix from line")
        result_lines.append(cleaned)

    return '\n'.join(result_lines)


def filter_out_fallback(response: str) -> str:
    """Try again with a different model if failing"""
    # TODO implement this, needs settings from agent, a bit complex, maybe not
    # suitable as a filter
    return response


def filter_out_sanity(response: str, max_repeat=80) -> str:
    """Truncate repeated characters to a maximum"""
    # Handle single character repetitions
    response = re.sub(rf'(.)\1{{{max_repeat-1},}}', lambda m: m.group(1) * (max_repeat-1), response)

    # Handle two character pattern repetitions (e.g., "ababab...")
    response = re.sub(rf'(..)\1{{{max_repeat//2-1},}}', lambda m: m.group(1) * (max_repeat//2-1), response)

    # Handle three character pattern repetitions (e.g., "abcabcabc...")
    response = re.sub(rf'(...)\1{{{max_repeat//3-1},}}', lambda m: m.group(1) * (max_repeat//3-1), response)

    return response


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
            response = filter_fn(response, *filter_args)  # type: ignore[arg-type]
            logger.debug("response after filter %r:\n%s", filter_name, response)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Agent %r: Error in filter_out %r: %s", agent.name, filter_name, str(e))

    return response


def apply_user_filters_out(user: str, content: str) -> str:
    """Apply output filters to the user's posted content."""
    # TODO use user agents, which inherit from a Human agent (normally)
    # For now, static list of filters for all users.
    filters = user_filter_out
    if not filters:
        return content

    for filter_name_item in filters:
        if isinstance(filter_name_item, list):
            filter_args = filter_name_item[1:]
            filter_name = filter_name_item[0]
        else:
            filter_args = []
            filter_name = filter_name_item

        filter_fn = filters_out.get(filter_name)
        if not filter_fn:
            logger.warning("User %r: Unknown user filter_out: %r", user, filter_name)
            continue

        try:
            logger.debug("content before user filter %r:\n%s", filter_name, content)
            content = filter_fn(content, *filter_args)  # type: ignore[arg-type]
            logger.debug("content after user filter %r:\n%s", filter_name, content)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("User %r: Error in user filter_out %r: %s", user, filter_name, str(e))

    return content


filters_in = {
    "think_add_example": filter_in_think_add_example,
    "think_brackets": filter_in_think_brackets,
}


filters_out = {
    "agents_install": filter_out_agents_install,
    "think_fix": filter_out_think_fix,
    "think_brackets": filter_out_think_brackets,
    "actions_reduce": filter_out_actions_reduce,
    "emojis": filter_out_emojis,
    "emdash": filter_out_emdash,
    "fix_image_prompts": filter_out_fix_image_prompts,
    "sanity": filter_out_sanity,
    # "fallback": filter_out_fallback,
}


# for post content from user
user_filter_out = [
    ["url_to_link_with_title", "h1"],
]

# for display to user / stream serice, e.g.:
# - totally block images
# TODO implement calling these when needed
user_filter_in = [
]

