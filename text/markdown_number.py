#!/usr/bin/env python3

"""
A tool to add or remove numbering from markdown headings or lists at given level/s
(or all levels by default).
"""

import sys
import re
from typing import TextIO, List, Dict, Tuple

from argh import arg

from ally import main

__version__ = "0.2.2"

logger = main.get_logger()


def process_line(line: str, level: int, remove: bool, list_mode: bool, number: int) -> str:
    """Process a single line for numbering or unnumbering."""
    if remove and list_mode:
        replacement = "- "
    elif remove:
        replacement = ""
    else:
        replacement = f"{number}. "

    if list_mode:
        pattern = r'^( *)(\d+\.|-)\s+'
    else:
        pattern = r'^(#+\s)\s*(\d+\.\s+)?'

    line = re.sub(pattern, lambda m: f"{m.group(1)}{replacement}", line)

    return line


def update_counters(
    counters: Dict[int, int], level: int, current_level: int
) -> Tuple[Dict[int, int], int]:
    """Update counters based on the current level."""
    logger.debug(f"Updating counters: {counters}, level: {level}, current_level: {current_level}")
    if level > current_level:
        counters[level] = 1
    elif level <= current_level:
        counters[level] += 1
    if level < current_level:
        counters[current_level] = 0
    logger.debug(f"Counters updated: {counters}")
    return counters, level


MAX_LEVEL = 100


@arg("levels", nargs="*", type=int, help="Heading or list levels to process (default: all)")
@arg("-r", "--remove", help="Remove numbering instead of adding it", action="store_true")
@arg("-l", "--list", dest="list_mode", help="Process numbered lists instead of headings", action="store_true")
def process_markdown(
    levels: List[int],
    input: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    remove: bool = False,
    list_mode: bool = False,
) -> None:
    """
    Add or remove numbering from markdown headings or lists at given level(s)
    (or all levels by default).
    """

    all_levels = range(0, MAX_LEVEL)

    if not levels:
        levels = range(0, MAX_LEVEL)

    counters = [0 for level in all_levels] + [0]
    real_levels = [0 for level in all_levels] + [0]

    current_level = 0
    real_level = 0

    logger.debug(f"input: {input}, output: {output}, remove: {remove}, list_mode: {list_mode}")

    for line in input:
        logger.debug(f"Processing line: {line}")
        if list_mode:
            pattern = r'^( *)(\d+\.\s+|-\s+)'
        else:
            pattern = r'^(#+)\s+(\d+\.\s+)?'

        match = re.match(pattern, line)
        if match:
            level = len(match.group(1))
            if level not in all_levels:
                logger.warning(f"Level too high: {level}")
            else:
                prev_level = current_level
                counters, current_level = update_counters(counters, level, current_level)
                logger.debug(f"Level: {level}, Counters: {counters}, will process line: {line}")
                if list_mode:
                    if current_level > prev_level:
                        real_level += 1
                    elif current_level < prev_level:
                        for i in range(current_level + 1, prev_level + 1):
                            real_levels[i] = 0
                        real_level = real_levels[current_level]
                else:
                    real_level = level
                real_levels[level] = real_level

                if real_level in levels:
                    line = process_line(line, level, remove, list_mode, counters[level])
        elif list_mode:
            # close list if not a list item
            indent = re.match(r'^( *)', line)
            indent = len(indent.group(1))
            if indent < current_level:
                for i in range(indent, current_level + 1):
                    counters[i] = 0
            elif current_level == 0 and re.match(r'^[^-\s]', line):
                counters[current_level] = 0

        output.write(line)
        # if log level is debug, flush after each line to see output in real time
        if logger.level == 10:
            output.flush()


if __name__ == "__main__":
    main.run(process_markdown)
