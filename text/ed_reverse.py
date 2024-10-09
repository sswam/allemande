#!/usr/bin/env python3

"""
This module processes an ed script, splitting it into separate commands
and sorting them in reverse numeric order by starting line number.
"""

import sys
import logging
from typing import TextIO
import re

from argh import arg

from ally import main

__version__ = "0.1.1"

logger = main.get_logger()


# block_commands = ['{', '}', 'a', 'i', 'c']
# line_commands = ['d', 'p', 'n', 'l', 'g', 'v', 's', 'q', 'r', 'w', 'e', 'f', 'x', 't', 'm', 'z', '!', 'P', 'N', 'L', 'G', 'V', 'S', 'Q', 'R', 'W', 'E', 'F', 'X', 'T', 'M', 'Z']

block_commands = ['a', 'i', 'c']
line_commands = ['d', 's']


Command = tuple[int, int, str, str]


def parse_ed_command(line: str) -> Command:
    """Parse an ed command and return start, end, and command type."""
    match = re.match(r'(\d+)(?:,(\d+))?([cdia])', line)
    if match:
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        command = match.group(3)
        return start, end, command
    raise ValueError(f"Invalid ed command: {line}")


def format_ed_command(start: int, end: int, command: str) -> str:
    """Format an ed command and return the formatted string."""
    if start == end:
        return f"{start}{command}"
    return f"{start},{end}{command}"


def process_ed_script(content: str) -> list[Command]:
    """Process the ed script and return a list of commands with line numbers."""
    lines = content.strip().split('\n')
    commands = []
    in_block = False
    current_command: list[str] | None = None

    for line in lines:
        if current_command is None and line.startswith('#'):
            continue
        if current_command is None:
            start, enc, command = parse_ed_command(line)
            if command in block_commands:
                in_block = True
                current_command = []
        elif line == '.' and in_block:
            commands.append((start, '\n'.join(current_command)))
            commands.append((start, end, command, '\n'.join(current_command)))
            current_command = None
            in_block = False
        elif current_command:
            current_command.append(line)
        else:
            raise ValueError(f"Invalid ed command: {line}")

    return commands


def check_overlap(sorted_commands: list[Command]) -> bool:
    """Check for overlapping commands and log an error if found."""
    for i in range(len(sorted_commands) - 1):
        current_start, current_cmd, _, _ = sorted_commands[i]
        next_start, _, _, _ = sorted_commands[i + 1]

        if current_cmd >= next_start:
            logger.error(f"{current_start=} {current_end=} {next_start=}")
            logger.error(f"Overlap detected between commands:\n{current_cmd}\nand\n{sorted_commands[i+1][1]}")
            return True
    return False


@arg("input_file", help="Input file containing ed script")
@arg("--output", help="Output file (default: stdout)")
def process_script(
    input_file: str,
    output: str | None = None,
) -> None:
    """
    Process an ed script, split it into separate commands,
    and sort them in reverse numeric order by starting line number.
    """
    try:
        with open(input_file, 'r') as f:
            content = f.read()
    except IOError as e:
        logger.error(f"Error reading input file: {e}")
        sys.exit(1)

    commands = process_ed_script(content)
    sorted_commands = sorted(commands, key=lambda x: x[0], reverse=True)

    if check_overlap(sorted_commands):
        sys.exit(1)

    output_content = '\n\n'.join(cmd for _, cmd in sorted_commands)

    ostream.write(output_content)


if __name__ == "__main__":
    main.run(process_script)


# TODO:
# s command
# look up other useful commands
