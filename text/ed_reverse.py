#!/usr/bin/env python3

"""
This module processes an ed script, splitting it into separate commands
and sorting them in reverse numeric order by starting line number.
"""

import sys
import re
from typing import TextIO

from ally import main  # type: ignore

__version__ = "0.1.6"

logger = main.get_logger()


# block_commands = ['{', '}', 'a', 'i', 'c']
# line_commands = ['d', 'p', 'n', 'l', 'g', 'v', 's', 'q', 'r', 'w', 'e', 'f', 'x', 't', 'm', 'z', '!', 'P', 'N', 'L', 'G', 'V', 'S', 'Q', 'R', 'W', 'E', 'F', 'X', 'T', 'M', 'Z']

block_commands = ["a", "i", "c"]
line_commands = ["d", "s"]

Command = tuple[int, int, str, str]


def parse_ed_command(line: str) -> Command:
    """Parse an ed command and return start, end, command type, and blank content."""
    match = re.match(r"(\d+)(?:,(\d+))?([cdias].*)", line)
    if match:
        start = int(match.group(1))
        end = int(match.group(2)) if match.group(2) else start
        command = match.group(3)
        return start, end, command, ""
    raise ValueError(f"Invalid ed command: {line}")


def format_ed_command(start: int, end: int, command: str, content: str) -> str:
    """Format an ed command with line numbers and content."""
    cmd = f"{start},{end}{command}" if start != end else f"{start}{command}"
    return f"{cmd}\n{content}.\n" if content else f"{cmd}\n"


def process_ed_script(content: str) -> list[Command]:
    """Process the ed script and return a list of commands with line numbers."""
    lines = content.strip().split("\n")
    commands: list[Command] = []
    current_command: Command | None = None

    for line in lines:
        if current_command is None and (
            line.startswith("#") or line.startswith("ed ") or line in ["w", "q"]
        ):
            continue
        if current_command is None:
            start, end, command, _content = parse_ed_command(line)
            current_command = (start, end, command, "")
            if command[0] in line_commands:
                commands.append(current_command)
                current_command = None
        elif line == "." and current_command[2][0] in block_commands:
            commands.append(current_command)
            current_command = None
        elif current_command:
            current_command = (*current_command[:3], current_command[3] + line + "\n")
        else:
            commands.append(current_command)
            current_command = None

    if current_command:
        commands.append(current_command)

    return commands


def check_overlap(sorted_commands: list[Command]) -> bool:
    """Check for overlapping commands and log an error if found."""
    for i in range(len(sorted_commands) - 1):
        next_start, _, _, _ = sorted_commands[i]
        _, current_end, _, _ = sorted_commands[i + 1]

        if current_end >= next_start:
            logger.error("Overlap detected between commands:")
            logger.error("Command 1: %s", format_ed_command(*sorted_commands[i + 1]))
            logger.error("Command 2: %s", format_ed_command(*sorted_commands[i]))
            return True
    return False


def process_script(
    istream: TextIO,
    ostream: TextIO,
    pure: bool = False,
) -> None:
    """
    Process an ed script, split it into separate commands,
    and sort them in reverse numeric order by starting line number.
    """
    content = istream.read()

    commands = process_ed_script(content)
    sorted_commands = sorted(commands, key=lambda x: x[0], reverse=True)

    if check_overlap(sorted_commands):
        logger.error("Overlapping commands detected")
        sys.exit(1)

    output_content = "".join(format_ed_command(*cmd) for cmd in sorted_commands)

    if not pure:
        output_content += "w\nq\n"

    ostream.write(output_content)


def setup_args(arg):
    """Set up the command line arguments."""
    arg("-p", "--pure", action="store_true", help="omit 'w' and 'q' commands at the end")


if __name__ == "__main__":
    main.go(process_script, setup_args)
