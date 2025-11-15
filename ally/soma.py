"""
Soma - Suboptimally (macro processor)
"""

import regex
from typing import Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# def person(name:str, clothes:str|None=None, emo:str|None=None age:str|None=None) -> str:
# 	"""return an unprompted macro for this"""
# 	return 


MACROS = {
		# "person": person,
}


def parse_macro_call(replacement: str, match: regex.Match, macros_dict: dict) -> str:
    """
    Parse and execute \\macro(arg1, arg2) calls in replacement string.
    """
    def replace_call(m):
        macro_name = m.group(1)
        args_str = m.group(2)

        if macro_name not in macros_dict:
            return m.group(0)

        args = [arg.strip() for arg in args_str.split(',')] if args_str else []

        # Replace $N with capture groups and remove quotes
        resolved_args = []
        for arg in args:
            arg = arg.strip('"\'')
            arg = regex.sub(r'\$(\d+)', lambda m: match.group(int(m.group(1))), arg)
            resolved_args.append(arg)

        return macros_dict[macro_name](match, *resolved_args)

    pattern = r'\\([a-zA-Z_][a-zA-Z0-9_]*)\(([^)]*)\)'
    result = regex.sub(pattern, replace_call, replacement)
    result = result.replace('\\\\', '\\')
    return result


def normalize_replacement(replacement: str) -> str:
    """Convert $0, $1, $2, etc. to Python's \\g<0>, \\1, \\2 syntax."""
    def replace_group(match):
        group_num = match.group(1)
        if group_num is None:
            return "$"
        if group_num == '0':
            return r'\g<0>'
        return '\\' + group_num

    return regex.sub(r'\\\$|\$(\d+)', replace_group, replacement)


def apply_mappings(text: str, mapping: dict[str, str],
                   macros_dict: dict | None = None) -> str:
    """
    Apply all pattern->replacement pairs in parallel.

    mapping is {pattern: replacement, ...}
    Builds one combined regex and applies all at once.
    """
    if macros_dict is None:
        macros_dict = {}

    if not mapping:
        return text

    # Build combined regex: (pattern1)|(pattern2)|(pattern3)
    patterns = list(mapping.keys())
    for pattern in patterns:
        try:
            regex.compile(pattern)
        except regex.error as e:
            raise ValueError(f"Invalid regex pattern: {pattern}") from e

    combined = '|'.join("("+p+")" for p in patterns)

    def replacer(match):
        # Figure out which pattern matched by checking groups
        for i, pattern in enumerate(patterns):
            if match.group(i + 1) is not None:
                replacement = mapping[pattern]

                # Expand $N capture groups
                expanded = normalize_replacement(replacement)
                expanded = match.expand(expanded)

                # Parse and execute \\macro() calls
                return parse_macro_call(expanded, match, macros_dict)
        raise ValueError("No matching pattern found in replacer")

    return regex.sub(combined, replacer, text, flags=regex.DOTALL)


def sub(text_input: str, configs: list[dict[str, str]],
              macros_dict: dict | None = None,
              max_depth: int = 10) -> str:
    """
    Apply macro configs recursively until no more matches.

    Each config is a dict of {pattern: replacement, ...}
    All patterns in a config are applied in parallel.
    Then we recurse until text stops changing.

    Example:
        configs = [
            {
                r'(.*?) COL (.*)': r'\\col(\\person($1), \\person($2))',
                r'(?i)\\bALLY\\b': r'\\person(Ally)',  # Case-insensitive
            }
        ]
    """
    if macros_dict is None:
        macros_dict = MACROS

    configs = [c for c in configs if c]

    text = text_input

    logger.info("soma input:  %s", text_input)

    for depth in range(max_depth):
        original = text

        # Apply each config's mappings in parallel
        for config in configs:
            text = apply_mappings(text, config, macros_dict)

        if text == original:
            break

        logger.info("soma change: %s", text)
    else:
        logger.warning("Max recursion depth (%d) reached in soma", max_depth)

    return text

# 1. The argument parsing for macros in `ally/soma.py` does not correctly
# handle commas within quoted arguments. The use of `args_str.split(',')` in
# `parse_macro_call` will incorrectly split an argument like `"foo, bar"`. A
# more robust parsing method, perhaps using the `csv` module or a regex that
# respects quotes, would handle this correctly.
# 
# 2. The current implementation of macro expansion in `parse_macro_call` does
# not support nested macro calls, such as `\outer(\inner(arg))`. The inner call
# `\inner(arg)` is passed as a literal string to the outer macro. This may
# be an intentional design choice for simplicity, but it's a limitation to be
# aware of.
