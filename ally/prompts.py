#!/usr/bin/env python3-allemande

"""
A library to add prompts into an LLM input message stream.

Provides functionality to manage and inject prompts at specific positions
in a message history, with support for variable substitution.
"""

from typing import Any
import re

from ally import logs

__version__ = "0.1.1"

logger = logs.get_logger()


def format_prompt_text(text: str, variables: dict[str, str] | None = None) -> str:
    """Format prompt text with variable substitution.

    Args:
        text: The prompt text to format
        variables: Dictionary of variables to substitute (e.g., {'NAME': 'Ally'})

    Returns:
        Formatted text with variables replaced
    """
    if not variables:
        return text

    for key, value in variables.items():
        text = text.replace(f"${key}", value)
    return text


def prompt_to_message(
    prompt_data: dict[str, Any],
    variables: dict[str, str] | None = None
) -> str:
    """Convert prompt data to a message format.

    Args:
        prompt_data: Dictionary containing 'text' and optional 'role'
        variables: Dictionary of variables to substitute

    Returns:
        Message in the format "role:\\ttext" or just "text" if no role
    """
    text = prompt_data.get("text", "")
    role = prompt_data.get("role")

    formatted_text = format_prompt_text(text, variables)

    if role:
        formatted_role = format_prompt_text(role, variables)
        return f"{formatted_role}:\t{formatted_text}"
    return formatted_text


def inject_prompts(
    messages: list[str],
    prompts_config: dict[str, dict[str, Any]],
    prompt_names: list[str] | None = None,
    variables: dict[str, str] | None = None
) -> list[str]:
    """Inject prompts into a message list at their specified positions.

    Args:
        messages: List of existing messages
        prompts_config: Dictionary mapping prompt names to their configuration
        prompt_names: List of prompt names to inject (None = inject all)
        variables: Dictionary of variables for substitution

    Returns:
        New list with prompts injected at appropriate positions
    """
    if prompt_names is None:
        prompt_names = list(prompts_config.keys())

    # Collect prompts with their positions
    prompts_to_inject: list[tuple[int, str, dict[str, Any]]] = []
    for name in prompt_names:
        if name not in prompts_config:
            continue
        prompt_data = prompts_config[name]
        pos = prompt_data.get("pos", 0)
        prompts_to_inject.append((pos, name, prompt_data))

    # Sort by position
    prompts_to_inject.sort(key=lambda x: x[0])

    result = messages.copy()
    n_messages = len(result)

    for pos, name, prompt_data in prompts_to_inject:
        message = prompt_to_message(prompt_data, variables)

        # Calculate actual insertion position
        if pos < 0:
            # Negative positions count from the end
            insert_pos = max(0, n_messages + pos + 1)
        else:
            # Positive positions count from the start
            insert_pos = min(pos, n_messages)

        result.insert(insert_pos, message)
        n_messages += 1

        logger.debug("Injected prompt %r at position %d", name, insert_pos)

    return result


def extract_variables(text: str) -> set[str]:
    """Extract variable names from text (e.g., $NAME, $FULLNAME).

    Args:
        text: Text containing variables in $VAR format

    Returns:
        Set of variable names found (without the $ prefix)
    """
    return set(re.findall(r'\$([A-Z_][A-Z0-9_]*)', text))

# ## Usage
#
# Instead of:
# 
# library = load_prompts(prompts_config)
# messages = library.inject(messages, ["main", "story"], {"NAME": "Ally", "FULLNAME": "Allemande"})
# 
# # Now use:
# 
# messages = inject_prompts(messages, prompts_config, ["main", "story"], {"NAME": "Ally", "FULLNAME": "Allemande"})
# 
# # Or to inject all prompts:
# 
# messages = inject_prompts(messages, prompts_config, variables={"NAME": "Ally", "FULLNAME": "Allemande"})
