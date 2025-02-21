#!/usr/bin/env python3-allemande

"""
Detect and apply indentation styles

This module can detect the indentation type and level of input text,
and can also reindent the input according to specified parameters.
"""

import os
import sys
import re
import argparse
from typing import TextIO, Callable
from collections import Counter
from functools import reduce

from ally import main, geput

__version__ = "1.0.2"

logger = main.get_logger()


# TODO use a config file for this?
def default_indent() -> str:
    ft = os.environ.get("FILETYPE")
    if ft == "python":
        return "4s"
    elif ft == "c":
        return "t"
# TODO: vim captures stderr, so we can't log to stderr here
#     elif ft:
#         logger.warning(f"Standard indentation not known for filetype: {ft}")
    return os.environ.get("INDENT", "t")


DEFAULT_INDENT = default_indent()


def find_common_indent(lines: list[str]) -> str:
    """ Find the common indentation among all lines. """
    common_indent = None
    for line in lines:
        if not line.strip():
            continue
        indent_size = len(line) - len(line.lstrip())
        indent = line[:indent_size]
        if common_indent is None:
            common_indent = indent
        else:
            common_indent = common_indent[: len(os.path.commonprefix([common_indent, indent]))]

    if common_indent is None:
        common_indent = ""
    return common_indent


def detect_indent(text: str | list[str]) -> tuple[int, str, int]:
    """Detect the indentation type and minimum level of the input text."""
    if isinstance(text, list):
        lines = text
    else:
        lines = text.splitlines()

    # Remove empty lines and get non-empty lines
    lines = [line for line in lines if line.strip()]

    # Find the common indentation among all lines
    common_indent = find_common_indent(lines)

    # Check for invalid indentation characters
    if re.search(r"[^\s\t]", common_indent):
        raise ValueError("Whitespace other than spaces and tabs in indentation")

    if "\t" in common_indent and " " in common_indent:
        raise ValueError("Mixed tabs and spaces in common indentation")

    common_indent_length = len(common_indent)

    # Remove common indentation from all lines
    stripped_lines = [line[common_indent_length:] for line in lines]

    # Count spaces and tabs at the beginning of each line
    spaces = re.compile(r"^ +")
    tabs = re.compile(r"^\t+")

    space_counts = [
        len(spaces.match(line).group()) if spaces.match(line) else 0
        for line in stripped_lines
    ]
    tab_counts = [
        len(tabs.match(line).group()) if tabs.match(line) else 0
        for line in stripped_lines
    ]

    logger.debug(space_counts)
    logger.debug(tab_counts)
    total_spaces = sum(space_counts)
    total_tabs = sum(tab_counts)

    # Helper function to find the greatest common divisor
    def find_common_factor_two(a, b):
        while b:
            a, b = b, a % b
        return a

    def find_common_factor(args):
        return reduce(find_common_factor_two, args)

    def not_none(list):
        return [x for x in list if x is not None]

    indent_size_freq = Counter(
        count for count in space_counts if count > 0 and count <= 8
    ).most_common(2)

    # Determine indentation type and size based on counts and common indentation
    if not common_indent and total_spaces == total_tabs == 0:
        indent_type = ""
        indent_size = 0
    elif "\t" in common_indent or total_tabs * 2 > total_spaces:
        indent_type = "t"
        indent_size = 1
    elif not indent_size_freq:
        indent_type = "s"
        if common_indent_length % 4 == 0:
            indent_size = 4
        elif common_indent_length % 2 == 0:
            indent_size = 2
        else:
            indent_size = 1
    else:
        # This isn't 100% because they can have 'continued lines' indented weirdly.
        indent_type = "s"
        indent_size = indent_size_freq[0][0]
        indent_size_2 = indent_size_freq[1][0] if len(indent_size_freq) > 1 else None
        indent_size = find_common_factor(not_none([indent_size, indent_size_2, common_indent_length]))
        if indent_size == 1:
            logger.debug("Indent detected is one space, sounds like a bad idea")
            indent_size = 4

    # Calculate the minimum indentation level
    min_level = common_indent_length // indent_size if indent_size else 0

    assert (
        indent_type != "t" or indent_size == 1
    ), f"Indent type is tab but indent size is not 1: {indent_size}"

    logger.debug(f">> {indent_size=}, {indent_type=}, {min_level=}")

    return indent_size, indent_type, min_level


def apply_indent(text: str, indent_size: int, indent_type: str, min_level: int) -> str:
    """Apply the specified indentation to the input text."""

    # Detect the original indentation of the input text
    orig_indent_size, orig_indent_type, orig_min_level = detect_indent(text)

    lines = text.splitlines()

    # Create indent strings for original and new indentation
    orig_indent_str = "\t" if orig_indent_type == "t" else " " * orig_indent_size
    orig_min_indent = orig_indent_str * orig_min_level

    indent_str = "\t" if indent_type == "t" else " " * indent_size
    min_indent = indent_str * min_level

    def reindent_line(line: str) -> str:
        # Remove trailing whitespace and original minimum indentation
        line = line.rstrip()
        line_without_min_indent = line[len(orig_min_indent) :]

        # Extract indentation and text content of the line
        line_indent_str, line_text = re.match(r"^(\s*)(.*)$", line_without_min_indent).groups()
        line_indent = len(line_indent_str) // orig_indent_size if orig_indent_size else 0

        # Apply new indentation
        new_indent = min_indent + indent_str * line_indent
        new_line = new_indent + line_text
        return new_line

    # Apply reindentation to all lines and join them
    return "\n".join(reindent_line(line) for line in lines) + "\n"


def format_indent_code(indent_size: int, indent_type: str, min_level: int) -> str:
    """Format the indent code for display."""
    # Convert indentation parameters to a string representation
    min_level_str = str(min_level) if min_level else ""
    if indent_type == "t":
        if indent_size != 1:
            raise ValueError(f"Invalid indent size for tab: {indent_size}")
        return f"t{min_level_str}"
    return f"{indent_size}s{min_level_str}"


def parse_indent_code(indent_code: str) -> tuple[int, str, int]:
    """Parse the indent code into its components."""
    # Extract indent size, type, and minimum level from the indent code string
    match = re.match(r"(\d*)(t|s)(\d*)$", indent_code)
    if not match:
        raise ValueError(f"Invalid indent code: {indent_code}")
    indent_size, indent_type, min_level = match.groups()
    if not indent_size:
        indent_size = 4 if indent_type == "s" else 1
    indent_size = int(indent_size)
    if indent_type == "t" and indent_size != 1:
        raise ValueError(f"Invalid indent size for tab: {indent_size}")
    if indent_type == "s" and indent_size > 8:
        raise ValueError(f"Invalid indent size for spaces: {indent_size}")
    if indent_type == 's' and indent_size not in {1, 2, 4}:
        logger.warning(f"Inadvisable indent size for spaces: {indent_size}")
    return indent_size, indent_type, int(min_level or 0)


def aligno(
    get: geput.Get,
    put: geput.Put,
    detect: bool = False,
    apply: bool = False,
    indent_code: str = DEFAULT_INDENT,
) -> None:
    """
    Detect or apply indentation to the input text.

    Environment:
        INDENT: default indent to use when not specified
        FILETYPE: use standard indentation for this language (python or c)

    Examples:
        aligno < input.txt
        aligno --apply < input.c > output.c
        aligno --apply 4s2 < input.py > output.py
    """

    print = geput.print(put)

    # Determine whether to detect or apply indentation
    indent_code = indent_code or DEFAULT_INDENT
    if apply and detect:
        raise ValueError("Cannot detect and apply indent at the same time")
    if not apply and not detect:
        detect = True

    input_text = geput.whole(get)

    if detect:
        # Detect and output the indentation of the input text
        detected_indent = detect_indent(input_text)
        indent_code = format_indent_code(*detected_indent)
        if indent_code.startswith("0"):
            indent_code = DEFAULT_INDENT
        print(indent_code)
    else:
        # Apply the specified or default indentation to the input text
        output_text = apply_indent(input_text, *parse_indent_code(indent_code))
        put(output_text)


def setup_args(parser: argparse.ArgumentParser) -> None:
    """Set up the command-line arguments."""
    parser.description = "Detect or apply indentation to the input text."
    parser.add_argument("--detect", "-D", action="store_true", help="detect indent type and minimum level")
    parser.add_argument("--apply", "-a", action="store_true", help="apply specified indent type and minimum level")
    parser.add_argument("indent_code", nargs="?", help="indent code (e.g., '1t', '4s2')")


if __name__ == "__main__":
    main.go(aligno, setup_args)
