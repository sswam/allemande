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

VERSION = "0.1.5"

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


def _extract_balanced_parens(text: str, start: int) -> tuple[int, int] | None:
    """
    Extract balanced parentheses content starting at position start.

    Returns (content_start, content_end) or None if unbalanced.
    """
    if start >= len(text) or text[start] != '(':
        return None

    depth = 0
    i = start

    while i < len(text):
        if text[i] == '(':
            depth += 1
        elif text[i] == ')':
            depth -= 1
            if depth == 0:
                return (start + 1, i)
        elif text[i] == '\\' and i + 1 < len(text):
            i += 1
        i += 1

    return None


def parse_macro_call(replacement: str, match: regex.Match, macros_dict: dict) -> str:
    """
    Parse and execute \\macro(arg1, arg2) calls in replacement string.
    Handles nested parentheses in arguments by recursively expanding them.
    """
    # The iterative loop is replaced by recursion in _execute_macro
    # to handle nested macro calls correctly (inside-out evaluation).
    result_text, _ = _process_text(replacement, match, macros_dict)
    return result_text


def _process_text(text: str, match: regex.Match, macros_dict: dict) -> tuple[str, bool]:
    """Process text and return (processed_text, changed_flag)."""
    result = []
    i = 0
    changed = False

    while i < len(text):
        macro_match = _try_match_macro(text, i, match, macros_dict)

        if macro_match:
            replacement_text, new_index = macro_match
            result.append(replacement_text)  # pyrefly: ignore
            i = new_index
            changed = True
        else:
            result.append(text[i])  # pyrefly: ignore
            i += 1

    return ''.join(result), changed


def _try_match_macro(text: str, i: int, match: regex.Match, macros_dict: dict) -> tuple[str, int] | None:
    """
    Try to match a macro at position i.
    Returns (replacement_text, next_index) or None if no match.
    """
    if not _is_macro_start(text, i):
        return None

    macro_name, macro_end = _extract_macro_name(text, i + 1)

    if not _has_opening_paren(text, macro_end):
        return None

    balanced = _extract_balanced_parens(text, macro_end)
    if not balanced:
        return None

    content_start, content_end = balanced

    if macro_name not in macros_dict:
        return text[i:content_end + 1], content_end + 1

    replacement = _execute_macro(text, content_start, content_end, macro_name, match, macros_dict)
    return replacement, content_end + 1


def _is_macro_start(text: str, i: int) -> bool:
    """Check if position i starts a macro (backslash followed by valid char)."""
    return text[i] == '\\' and i + 1 < len(text)


def _extract_macro_name(text: str, start: int) -> tuple[str, int]:
    """Extract macro name starting at position start. Returns (name, end_index)."""
    end = start
    while end < len(text) and (text[end].isalnum() or text[end] == '_'):
        end += 1
    return text[start:end], end


def _has_opening_paren(text: str, pos: int) -> bool:
    """Check if there's an opening parenthesis at position pos."""
    return pos < len(text) and text[pos] == '('


def _execute_macro(text: str, content_start: int, content_end: int,
                macro_name: str, match: regex.Match, macros_dict: dict) -> str:
    """Execute a macro with its arguments."""
    args_str = text[content_start:content_end]

    # Recursively expand macros in the arguments first (inside-out evaluation).
    expanded_args_str = parse_macro_call(args_str, match, macros_dict)
    args = _parse_macro_args(expanded_args_str)

    resolved_args = _resolve_args(args, match)
    return macros_dict[macro_name](match, *resolved_args)


def _resolve_args(args: list[str], match: regex.Match) -> list[str]:
    """Resolve macro arguments by removing quotes and substituting capture groups."""
    resolved = []
    for arg in args:
        arg = arg.strip('"\'')
        arg = regex.sub(r'\$(\d+)', lambda n: match.group(int(n.group(1))), arg)
        resolved.append(arg)
    return resolved


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
        flags=regex.DOTALL|regex.MULTILINE|regex.IGNORECASE # pyrefly: ignore
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
