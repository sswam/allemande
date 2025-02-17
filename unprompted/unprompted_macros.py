"""Module for parsing macro definitions in text with form [name key=value]"""

import re
import copy


CAN_COMBINE = set(["sets"])


def unescape_string(value: str) -> str:
    """
    Unescape a quoted string value with C-style escapes.

    Args:
        value: String to unescape

    Returns:
        Unescaped string
    """
    escapes = {
        "n": "\n",
        "t": "\t",
        "\\": "\\",
        '"': '"',
        "'": "'",
    }

    result = []
    i = 0
    while i < len(value):
        if value[i] == "\\" and i + 1 < len(value):
            escaped_char = value[i + 1]
            result.append(escapes.get(escaped_char, escaped_char))
            i += 2
        else:
            result.append(value[i])
            i += 1

    return "".join(result)


def parse_macro_block(text: str, start: int) -> tuple[str, dict[str, str], int]:
    """
    Parse a single macro block starting at the given position.
    Returns macro name, key-value pairs, and ending position.

    Args:
        text: Input text containing the macro
        start: Starting position of the macro

    Returns:
        Tuple of (macro_name, key_value_pairs, end_position)
    """
    # Extract macro name
    name_end = text.find(" ", start + 1)
    if name_end == -1:
        # Check if this is an empty macro
        close_pos = text.find("]", start + 1)
        if close_pos == -1:
            raise ValueError("Unclosed macro block")
        macro_name = text[start + 1 : close_pos]
        if not macro_name:
            raise ValueError("Invalid macro format - no name")
        return macro_name, {}, close_pos

    macro_name = text[start + 1 : name_end]
    if not macro_name:
        raise ValueError("Invalid macro format - no name")

    # Find closing bracket
    pos = name_end
    in_quotes = False
    quote_char = None

    while pos < len(text):
        if text[pos] == "\\" and in_quotes:
            pos += 2
            continue

        char = text[pos]
        if char in "\"'":
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
        elif char == "]" and not in_quotes:
            break

        pos += 1

    if pos >= len(text):
        raise ValueError("Unclosed macro block")

    # Parse content
    content = text[name_end:pos].strip()
    pairs = parse_key_value_pairs(content)

    return macro_name, pairs, pos


def parse_macros(text: str) -> dict[str, dict[str, str]]:
    """
    Parse all macros in text and return dictionary of macro definitions.
    Each macro has form [name key1=value1 key2=value2].
    Values may be quoted with escapes.

    Examples:
        >>> parse_macros("[sets a=1 b=2][other x='hello']")
        {'sets': {'a': '1', 'b': '2'}, 'other': {'x': 'hello'}}

    Args:
        text: Input text containing macros

    Returns:
        Dictionary mapping macro names to their key-value pairs
    """
    result: dict[str, dict[str, str]] = {}
    pos = 0

    while True:
        start = text.find("[", pos)
        if start == -1:
            break

        try:
            name, pairs, end_pos = parse_macro_block(text, start)
            if name in result:
                result[name].update(pairs)
            else:
                result[name] = pairs
            pos = end_pos + 1

        except ValueError:
            pos = start + 1

    return result


def parse_key_value_pairs(content: str) -> dict[str, str]:
    """
    Parse a string of key-value pairs into a dictionary.
    Handles quoted values with escape sequences and bare keys without values.

    Args:
        content: String containing key=value pairs or bare keys

    Returns:
        Dictionary of parsed key-value pairs
    """
    pairs = {}
    # First handle key=value pairs
    pair_pattern = r"""
        (\w+)\s*=\s*
        (?:
            ["'](((?:\\["']|[^"'])*?))["\']  # Quoted value with escapes
            |
            (\S+)         # Unquoted value
        )
    """

    pos = 0
    for match in re.finditer(pair_pattern, content, re.VERBOSE):
        key = match.group(1)
        value = match.group(2) if match.group(2) is not None else match.group(4)
        if match.group(2) is not None:
            value = unescape_string(value)
        pairs[key] = value
        pos = match.end()

    # Then handle any remaining bare keys
    remainder = content[pos:].strip()
    if remainder:
        # Split on whitespace and treat each word as a key with None value
        for key in remainder.split():
            if key:
                pairs[key] = None

    return pairs


def update_macros(prompt: str, settings: dict[str, dict[str, str]]) -> str:
    """
    Update or add macros in the prompt string based on the provided settings.

    Args:
        prompt: Input prompt text containing macros
        settings: Dictionary mapping macro names to key-value pairs to update

    Returns:
        Updated prompt string with modified macros
    """
    settings = copy.deepcopy(settings)
    result = prompt
    for macro_name, macro_settings in list(settings.items()):
        # Preserve existing macros
        existing_macros = list(re.finditer(rf"\[{macro_name}(?:\s+[^\]]+)?\]", result))

        if existing_macros:
            # Update each existing macro instance individually
            for match in reversed(existing_macros):
                start, end = match.span()
                current_settings = parse_key_value_pairs(match.group()[len(macro_name) + 2 : -1])
                # Preserve existing settings while applying updates
                for key in list(macro_settings.keys()):
                    if key in current_settings or macro_name in CAN_COMBINE:
                        current_settings[key] = macro_settings[key]
                        del macro_settings[key]

                macro_str = f"[{macro_name}"
                for key, value in current_settings.items():
                    if value is None:
                        macro_str += f" {key}"
                    else:
                        formatted_value = f'"{value}"' if " " in str(value) else value
                        macro_str += f" {key}={formatted_value}"
                macro_str += "]"
                result = result[:start] + macro_str + result[end:]

        if macro_settings:
            # Add new macro at end
            if result and not result.endswith(" "):
                result += " "
            macro_str = f"[{macro_name}"
            for key, value in macro_settings.items():
                if value is None:
                    macro_str += f" {key}"
                else:
                    formatted_value = f'"{value}"' if " " in str(value) else value
                    macro_str += f" {key}={formatted_value}"
            macro_str += "]"
            result += macro_str

    return result.strip()
