"""
This module provides filters for processing chat input and output messages, and installing agents.
"""

import random
import re
from pathlib import Path

import regex

from ally import logs  # type: ignore
import ally_agents  # type: ignore
import settings  # type: ignore
import util  # type: ignore
from text.unsmart import unsmart, smart  # type: ignore


__version__ = "0.1.4"

logger = logs.get_logger()

def filter_out_agents_install(message: str, root: str = "") -> str:
    """Install agents from a message by extracting YAML blocks and saving them to files."""
    logger.debug("filter_out_agents_install input message:\n\n%s", message)

    # remove indent and role label
    dedented_message = re.sub(r"^.*?\t", "", message, flags=re.MULTILINE)

    # Extract YAML blocks
    yaml_blocks = regex.findall(
        r"```yaml\n(.*?)```",
        dedented_message,
        flags=regex.DOTALL | regex.IGNORECASE
    )

    all_yaml = "".join(yaml_blocks)
    logger.debug("Found %d YAML blocks in message: %r", len(yaml_blocks), yaml_blocks)

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
            logger.warning("Successfully installed agent: %s", file_path)

        except (OSError, IOError) as e:
            logger.error("Failed to write agent file %s: %s", file_path, str(e))

    return message


def filter_in_think_add_example(message: str, place: int, example: str = "I was thinking... what was I thinking...?") -> str:
    """Add an example <think> section to the message, if not already present."""
    # TODO make sure it's own message, not another agent's message
    # TODO maybe not needed?
    if place == 1 and "<think>" not in message:
        message = re.sub("\t", f"\t<think>{example}</think>\n\t", message, count=1)
    return message


def filter_in_think_brackets(message: str, place: int) -> str:
    """Replace <think>thinking sections</think> with [thinking sections]."""
    message = re.sub(r"<think>(.*?)</think>", lambda thought: f"[{thought.group(1).strip()}]", message, flags=re.DOTALL)
    return message


def filter_in_clean_up_mentions(message: str, place: int) -> str:
    """
    1. Replace e.g. @Ally with Ally
    2. Strip leading @+over or @^base from line
    """
    message = re.sub(r"(\s)@(\w)", r"\1\2", message)
    message = re.sub(r"^@[+^]\w+\s", "", message)
    return message


def clean_up_input_message(message: str) -> str:
    """
    1. Squash multiple blank lines into a single blank line
    2. If message content is empty, i.e. message is only Name:\t\s*, remove it
    3. Strip
    """
    message = re.sub(r'\n{3,}', '\n\n', message)
    message = re.sub(r'^.*?:\t\s*$', '', message)
    message = message.strip()
    return message


def filter_in_remove_images(message: str, _place: int) -> str:
        """
        Remove ![...](...) images, and squash blank lines.
        """
        # Remove markdown images: ![alt text](url)
        message = re.sub(r'!\[([^\]]*)\]\([^\)]*\)', '', message)

        message = clean_up_input_message(message)

        return message


def filter_in_remove_code(message: str, _place: int) -> str:
        """
        Remove ``` ... ``` code, and squash blank lines.
        """
        # Remove fenced code blocks: ```...``` (``` might not be at start of a line)
        message = re.sub(r'```.*?```', '', message, flags=re.DOTALL)

        message = clean_up_input_message(message)

        return message


def filter_out_think_brackets(message: str) -> str:
    """Replace [thinking sections] with <think>thinking sections</think>."""
    # match at start and end of lines only, so we don't match images / links
    message = re.sub(r"\t\[(.*?)\]$", r"\t<think>\1</think>", message, flags=re.DOTALL|re.MULTILINE)
    return message


def filter_out_think_fix(message: str) -> str:
    """Fix nesting and formatting of <think></think> containers.
    Ensures there is always a newline immediately after the closing </think> tag.
    """
    logger.info("filter_think_fix 1 input: %s", message)

    # Extract all text between first <think> and last </think>
    think_pattern = r'<think>(.*)</think>'
    match = re.search(think_pattern, message, flags=re.DOTALL)

    if not match:
        logger.info("filter_think_fix 2: no think tags found")
        return message

    logger.info("filter_think_fix 2 found think tags: %s", match.group(0)[:100])

    # Get the content and position
    think_content = match.group(1)
    start_pos = match.start()
    end_pos = match.end()

    # Remove any nested <think> or </think> tags from content, preserving everything else
    cleaned_content = re.sub(r'</?think>', '', think_content)
    logger.info("filter_think_fix 3 after removing nested tags: %s", cleaned_content[:100])

    # Get text before and after
    before = message[:start_pos]
    after = message[end_pos:]

    # Split before into lines to analyze the last line
    lines_before = before.split('\n')
    last_line = lines_before[-1] if lines_before else ''

    # Check if last line is just a label (e.g., "Acsi:" or "Assistant:")
    is_label_line = bool(last_line.strip()) and not before.endswith('\n')

    # Build result up to and including </think>
    if is_label_line:
        # Keep the label on same line with a tab before <think>
        before = before.rstrip()
        result = f"{before}\t<think>{cleaned_content}</think>"
    else:
        # Standard case: put <think> on new line
        before = before.rstrip()
        result = before
        if result and not result.endswith('\n'):
            result += '\n'
        result += f"<think>{cleaned_content}</think>"

    # Ensure exactly one newline immediately after </think>
    if after.startswith('\n') or after.startswith('\r\n'):
        # Already has a newline; do not add another
        result += ''
    else:
        result += '\n'

    # Add remaining content
    if after:
        result += after

    logger.info("filter_think_fix 4 output: %s", result)

    return result


def filter_out_actions_reduce(message: str, keep_prob: float = 0.5) -> str:
    """Reduce the number of *actions* in the message, based on keep_prob (0-1)."""
    logger.warning("filter_out_actions_reduce: %r %s", keep_prob, message)
    message2 = re.sub(r"( *)\*\w[^*]*? [^*]*?[^*\s*]\*[.!?]* *",
        lambda action: action.group(0) if random.random() < keep_prob else " ",
        message, flags=re.DOTALL)
    logger.warning("  %s", message2)

    # Strip spaces and reduce blank lines
    message2 = re.sub(r"^\t +", "\t", message2, flags=re.MULTILINE)
    message2 = re.sub(r" +$", "", message2, flags=re.MULTILINE)
    message2 = re.sub(r"\n{3,}", "\n\n", message2)

    if message2 and not re.search(r":\t?$", message2):
        return message2
    return message


def filter_out_actions_fix(message: str) -> str:
    """Attempt to fix *actions* syntax in the message."""
    logger.warning("filter_out_actions_fix: processing message:\n%s", message)
    lines = message.split("\n")
    for i in range(len(lines)):
        line = lines[i]

        match = re.match(r"(.*?\t)(.*)", line)
        if match:
            prefix, content = match.group(1), match.group(2)
        else:
            prefix, content = '', line

        content0 = content

        logger.warning("filter_out_actions_fix: processing content: %s", content)

        start_star = content.startswith("*")
        end_star = content.endswith("*")

        # Add missing * at start
        if not start_star and re.match("^[^*]+\S\*", content):
            content = "*" + content
            start_star = True
        # Add missing * at end
        if not end_star and re.search("\*\w[^*]+$", content):
            content = content + "*"
            end_star = True
        # Remove unmatched * at start
        if start_star and not re.match("\*[^*]+\S\*", content):
            content = content[1:]
            start_star = False
        # Remove unmatched * at end
        if end_star and not re.search("\*\w[^*]+\*$", content):
            content = content[:-1]
            end_star = False

        if content != content0:
            logger.warning("  changed to: %s", content)

            lines[i] = prefix + content

    message = "\n".join(lines)

    return message


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


def filter_out_emojis(message: str, keep_prob: float = 0.0) -> str:
    """Reduce the number of emojis in the message, based on keep_prob (0-1)."""
    if keep_prob == 0.0:
        return RE_EMOJIS.sub('', message)
    if keep_prob == 1.0:
        return message
    return RE_EMOJIS.sub(lambda m: m.group(0) if random.random() < keep_prob else '', message)


def filter_out_emdash(message: str, keep_prob: float = 0.0, replacement: str = " - ") -> str:
    """Replace em-dash characters with a replacement string, based on keep_prob (0-1)."""
    # Handle different types of em-dashes and their Unicode variants
    # includes em-dash, en-dash, and horizontal bar, strips surrounding spaces
    emdash_pattern = r'( *)(?:[-\u2014\u2013\u2015] *?)+( *)'

    if keep_prob == 0.0:
        return re.sub(emdash_pattern, r"\1"+replacement+r"\2", message)
    if keep_prob == 1.0:
        return message
    return re.sub(emdash_pattern, lambda m: m.group(0) if random.random() < keep_prob else m.group(1)+replacement+m.group(2), message)


def filter_out_fix_image_prompts(message: str) -> str:
    """Fix image prompts generated by ... less formal syntax-oriented agents!"""
    art_model_default = "Coni"

    logger.info("filter_out_fix_image_prompts 1: %s", message)

    # Strip leading tabs from all lines
    lines = message.split('\n')
    message = '\n'.join(line.lstrip('\t') for line in lines)

    # First pass: collect and fix properly quoted image prompts
    quoted_prompts = list(regex.finditer(r"```\s*(.*?)```", message, flags=regex.DOTALL))

    if quoted_prompts:
        logger.info("Found %d quoted image prompt blocks", len(quoted_prompts))
        message = fix_quoted_prompts(message, quoted_prompts, art_model_default)
    else:
        logger.info("No quoted image prompts found, checking for unquoted prompts")
        message = find_and_fix_unquoted_prompts(message, art_model_default)

    # Clean up $ArtModel lines outside of prompts
    message = remove_art_model_lines(message)

    # Remove chat: prefix from lines
    message = remove_chat_prefix(message)

    # Prefix each line other than the first with a leading tab
    lines = message.split('\n')
    if len(lines) > 1:
        message = lines[0] + '\n' + '\n'.join('\t' + line for line in lines[1:])

    return message


def fix_quoted_prompts(message: str, quoted_prompts: list, art_model_default: str) -> str:
    """Fix already-quoted image prompts in place."""
    offset = 0
    for match in quoted_prompts:
        prompt_content = match.group(1).strip()

        if not is_image_prompt(prompt_content):
            continue

        logger.info("Fixing quoted prompt: %s...", prompt_content[:50])
        fixed_content = fix_prompt_content(prompt_content, art_model_default)

        # Replace in message accounting for offset changes
        start = match.start() + offset
        end = match.end() + offset
        replacement = f"```\n{fixed_content}\n```"
        message = message[:start] + replacement + message[end:]
        offset += len(replacement) - (end - start)

    return message


def find_and_fix_unquoted_prompts(message: str, art_model_default: str) -> str:
    """Find unquoted image prompts and wrap them in code blocks."""
    lines = message.split('\n')
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
    if not regex.match(r"^@?[A-Z]\w+,", prompt):
        logger.info("Adding default art model '%s' to prompt", art_model_default)
        prompt = f"@{art_model_default}, {prompt}"

    return prompt


def remove_art_model_lines(message: str) -> str:
    """Remove lines that begin with $ArtModel outside of code blocks."""
    lines = message.split('\n')
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


def remove_chat_prefix(message: str) -> str:
    """Remove chat: prefix from lines."""
    lines = message.split('\n')
    result_lines: list[str] = []

    for line in lines:
        cleaned = regex.sub(r"^chat:\s*", "", line)
        if cleaned != line:
            logger.info("Removed 'chat:' prefix from line")
        result_lines.append(cleaned)

    return '\n'.join(result_lines)


def filter_out_fallback(message: str) -> str:
    """Try again with a different model if failing"""
    # TODO implement this, needs settings from agent, a bit complex, maybe not
    # suitable as a filter
    return message


def filter_out_truncate_repeated_characters(message: str, max_repeat=80) -> str:
    """Truncate repeated characters to a maximum"""
    # Handle single character repetitions
    message = re.sub(rf'(.)\1{{{max_repeat-1},}}', lambda m: m.group(1) * (max_repeat-1), message)

    # Handle two character pattern repetitions (e.g., "ababab...")
    message = re.sub(rf'(..)\1{{{max_repeat//2-1},}}', lambda m: m.group(1) * (max_repeat//2-1), message)

    # Handle three character pattern repetitions (e.g., "abcabcabc...")
    message = re.sub(rf'(...)\1{{{max_repeat//3-1},}}', lambda m: m.group(1) * (max_repeat//3-1), message)

    return message


def filter_out_remove_indent(message: str) -> str:
    """
    Remove any indent with tabs in the message.
    This method isn't exactly correct, but good enough for the purpose.
    """
    lines = message.split("\n")
    for i in range(len(lines)):
        line = lines[i]

        match = re.match(r"(.*?\t)(.*)", line)
        if match:
            prefix, content = match.group(1), match.group(2)
        else:
            prefix, content = '', line

        content0 = content
        content = re.sub(r"\t", " ", content.strip())

        if content != content0:
            logger.warning("filter_out_remove_indent: %s", content0)
            logger.warning("  changed to: %s", content)

            lines[i] = prefix + content

    message = "\n".join(lines)

    return message


def filter_out_test_chat_loop(message: str) -> str:
    """
    Replace any @ mention with @Xilu, causes Xilu to always attempt a chat loop.
    This is only to aid debugging, not for actual use!
    """
    message = re.sub(r"@\w+", "@Xilu", message)
    return message


def apply_filters_in(agent: ally_agents.Agent, history: list[str]) -> list[str]:
    """Apply input filters to the query and history."""
    filters = agent.get("filter_in")
    if not filters:
        return history

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
            hist_len = len(history_new)
            # NOTE: history[-1] is similar to query, but with the username prefix
            for i in range(hist_len):
                history_new[i] = filter_fn(history_new[i], hist_len - i - 1, *filter_args)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Agent %r: Error in filter_in %r: %s", agent.name, filter_name, str(e))

    history_new = [x for x in history_new if x]

    return history_new


def apply_filters_out(agent: ally_agents.Agent, message: str) -> str:
    """Apply output filters to the message."""
    filters = agent.get("filter_out")
    if not filters:
        return message

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
            logger.debug("message before filter %r:\n%s", filter_name, message)
            message = filter_fn(message, *filter_args)  # type: ignore[arg-type]
            logger.debug("message after filter %r:\n%s", filter_name, message)
        except Exception as e:  # pylint: disable=broad-except
            logger.exception("Agent %r: Error in filter_out %r: %s", agent.name, filter_name, str(e))

    return message


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
    "clean_up_mentions": filter_in_clean_up_mentions,
    "remove_images": filter_in_remove_images,
    "remove_code": filter_in_remove_code,
}


filters_out = {
    "agents_install": filter_out_agents_install,
    "think_fix": filter_out_think_fix,
    "think_brackets": filter_out_think_brackets,
    "actions_reduce": filter_out_actions_reduce,
    "actions_fix": filter_out_actions_fix,
    "emojis": filter_out_emojis,
    "emdash": filter_out_emdash,
    "fix_image_prompts": filter_out_fix_image_prompts,
    "truncate_repeated_characters": filter_out_truncate_repeated_characters,
    "unsmart": unsmart,
    "smart": smart,
    "remove_indent": filter_out_remove_indent,
    "test_chat_loop": filter_out_test_chat_loop,
    # "fallback": filter_out_fallback,
}


# for post content from user
user_filter_out = []
#     ["url_to_link_with_title", "h1"],
# ]

# for display to user / stream serice, e.g.:
# - totally block images
# TODO implement calling these when needed
user_filter_in = [
]

