"""
Soma - Suboptimally (macro processor)
"""

import csv
import io
import re
import regex
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERSION = "0.1.2"

MACROS = {
    # "person": person,
}


def _parse_macro_args(args_str: str) -> list[str]:
    """Parse comma-separated arguments respecting quotes."""
    if not args_str:
        return []

    reader = csv.reader(io.StringIO(args_str), skipinitialspace=True)
    return next(reader)


def _do_macro_replacement(m: regex.Match, match: regex.Match, macros_dict: dict) -> str:
    """Helper for parse_macro_call - handles a single \\macro() match."""
    macro_name = m.group(1)
    args_str = m.group(2)

    if macro_name not in macros_dict:
        return m.group(0)

    args = _parse_macro_args(args_str)

    # Replace $N with capture groups and remove quotes
    resolved_args = []
    for arg in args:
        arg = arg.strip('"\'')
        arg = regex.sub(r'\$(\d+)', lambda n: match.group(int(n.group(1))), arg)
        resolved_args.append(arg)

    return macros_dict[macro_name](match, *resolved_args)


def parse_macro_call(replacement: str, match: regex.Match, macros_dict: dict) -> str:
    """
    Parse and execute \\macro(arg1, arg2) calls in replacement string.
    """
    # Match parentheses more carefully to handle nesting
    pattern = r'\\([a-zA-Z_][a-zA-Z0-9_]*)\(([^()]*)\)'

    def recursive_replace(text: str, depth: int = 0) -> str:
        if depth > 10:
            return text
        result = regex.sub(pattern, lambda m: _do_macro_replacement(m, match, macros_dict), text)
        if result == text:
            return result
        return recursive_replace(result, depth + 1)

    return recursive_replace(replacement)


def _normalize_group_ref(match: re.Match) -> str:
    """Helper for normalize_replacement - handles a single $N reference."""
    group_num = match.group(1)
    if group_num is None:
        return "$"
    if group_num == '0':
        return r'\g<0>'
    return '\\' + group_num


def normalize_replacement(replacement: str) -> str:
    """Convert $0, $1, $2, etc. to Python's \\g<0>, \\1, \\2 syntax."""
    return re.sub(r'\\\$|\$(\d+)', _normalize_group_ref, replacement)


def analyze_patterns(patterns: list[str]) -> list[tuple[str, int, int, int]]:
    """
    Analyze patterns to determine group structure.

    Returns list of (pattern, outer_group, inner_start, num_inner_groups).

    When patterns are combined as (pat0)|(pat1)|(pat2), we need to track:
    - outer_group: which group number contains this pattern's match (or None)
    - inner_start: group number where this pattern's first capture group starts
    - num_inner_groups: how many capture groups this pattern has
    """
    metadata = []
    current_group = 1  # Group 0 is always whole match

    for pattern in patterns:
        try:
            compiled = regex.compile(pattern)
        except Exception as e:  # pylint: disable=broad-except
            raise ValueError(f"Invalid regex pattern: {pattern}") from e

        num_inner = compiled.groups
        outer_group = current_group
        inner_start = current_group + 1

        metadata.append((pattern, outer_group, inner_start, num_inner))

        # Next pattern's outer group comes after this pattern's outer + all inner groups
        current_group = inner_start + num_inner

    return metadata


def _remap_single_ref(match: re.Match, inner_start: int, num_inner: int) -> str:
    """Helper for remap_group_refs - handles a single $N reference."""
    if match.group(0) == r'\$':
        return r'\$'  # Escaped dollar sign

    group_num = int(match.group(1))

    if group_num == 0:
        return '$0'  # Whole match - leave unchanged

    if group_num > num_inner:
        raise ValueError(
            f"Group ${group_num} referenced but pattern only has {num_inner} groups"
        )

    actual_group = inner_start + group_num - 1
    return f'${actual_group}'


def remap_group_refs(replacement: str, outer_group: int, inner_start: int,
                    num_inner: int) -> str:
    """
    Remap $N references in replacement string to actual group numbers.

    User writes $1, $2, etc. thinking of groups within their pattern.
    We need to adjust to actual group numbers in the combined regex.

    $0 stays as $0 (whole match).
    $N (N > 0) becomes $(inner_start + N - 1).
    """
    return re.sub(
        r'\\\$|\$(\d+)',
        lambda m: _remap_single_ref(m, inner_start, num_inner),
        replacement
    )


def _apply_one_match(match: regex.Match, metadata: list, mapping: dict,
                    macros_dict: dict) -> str:
    """Helper for apply_mappings - processes a single regex match."""
    for pattern, outer_group, inner_start, num_inner in metadata:
        if match.group(outer_group) is not None:
            replacement = mapping[pattern]

            # Remap $N to actual group numbers for this pattern
            remapped = remap_group_refs(replacement, outer_group,
                                    inner_start, num_inner)

            # Parse and execute \\macro() calls BEFORE expanding
            # This prevents match.expand from seeing invalid escapes like \p, \c
            expanded_macros = parse_macro_call(remapped, match, macros_dict)

            # Now expand $N capture groups
            normalized = normalize_replacement(expanded_macros)
            result = match.expand(normalized)

            return result

    raise ValueError("No matching pattern found in replacer")


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

    patterns = list(mapping.keys())

    # Analyze patterns to get group structure
    metadata = analyze_patterns(patterns)

    # Build combined regex: (pattern1)|(pattern2)|(pattern3)
    combined = '|'.join(f"({pattern})" for pattern, _, _, _ in metadata)

    return regex.sub(
        combined,
        lambda m: _apply_one_match(m, metadata, mapping, macros_dict),
        text,
        flags=regex.DOTALL|regex.MULTILINE  # pyrefly: ignore
    )


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
                r'(?i)\\bALLY\\b': r'\\person(Ally)',
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


# Known Issues:

# 1. The regex used to find macro calls in `parse_macro_call`,
# `r'\\... \(([^()]*)\)'`, does not account for parentheses within the argument
# list. As a result, a macro call like `\macro("hello (world)")` will not be
# found and expanded because the `[^()]*` part will not match past the opening
# parenthesis in `(world)`.
