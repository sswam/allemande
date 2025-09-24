"""
Utility functions
"""

import re


def dict_not_none(d: dict) -> dict:
    """Return a new dict with only the non-None values."""
    return {k: v for k, v in d.items() if v is not None}


def list_not_none(l: list) -> list:
    """Return a new list with only the non-None values."""
    return [v for v in l if v is not None]


def quiet_unless_debug(fn, *args, **kwargs):
    """Quiet stdout and stderr unless in debug mode."""
    # FIXME: Not tested
    if logs.level() <= logs.DEBUG:
        return fn(*args, **kwargs)
    with unix.redirect(stdout=None, stderr=None):
        return fn(*args, **kwargs)


def replace_variables(text, var_dict, preserve_code_blocks=True):
    """
    Replace variables in text while preserving code blocks.

    Args:
        text (str): The input text containing variables to replace
        var_dict (dict): Dictionary mapping variable names to their values
        preserve_code_blocks (bool): If True, preserve code blocks

    Returns:
        str: Text with variables replaced outside code blocks
    """

    if isinstance(text, list):
        return [replace_variables(t, var_dict, preserve_code_blocks) for t in text]
    if isinstance(text, dict):
        return {k: replace_variables(v, var_dict, preserve_code_blocks) for k, v in text.items()}
    if not isinstance(text, str):
        return text

    # Create patterns for each variable, properly escaped
    patterns = {
        re.escape(f"${key}") + r'\b': str(value).replace('\\', '\\\\')
        for key, value in var_dict.items()
    }

    if not preserve_code_blocks:
        # If not preserving code blocks, replace all variables
        for pattern, replacement in patterns.items():
            text = re.sub(pattern, replacement, text)
        return text

    lines = text.splitlines()
    in_code_block = False
    result = []

    for line in lines:
        # Check for code block markers
        if re.match(r'^\s*```\w*\s*$', line):
            in_code_block = not in_code_block
            result.append(line)
            continue

        if not in_code_block:
            # Perform all substitutions outside code blocks
            for pattern, replacement in patterns.items():
                line = re.sub(pattern, replacement, line)
            result.append(line)
        else:
            result.append(line)

    return '\n'.join(result)


# def clamp(x, a, b):
# 	return max(a, min(x, b))
