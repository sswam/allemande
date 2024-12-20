#!/usr/bin/env python3-allemande

"""
This module generates a help message for command-line options based on the script's content.
"""

import os
import sys
import re
import textwrap
import argparse
from typing import TextIO, Callable
from pathlib import Path

import sh

from ally import main, geput

__version__ = "0.1.2"

logger = main.get_logger()


def process_line(line: str, script_name: str) -> str:
    """Process a single line of the script."""
    # Remove indent
    # line = line.lstrip()

    logger.debug("Processing line: %s", line)

    # Remove 'local ' from start of line
    line = re.sub(r'^\s*local\s+', '', line)

    # Replace literal '$0' in lines with the value of script_name
    line = line.replace('$0 ', f'{script_name} ')

    if re.match(r'\s*#\s?', line):
        # Remove '#' from the line
        line = re.sub(r'^\s*#\s?', '', line)
    else:
        # Add dashes for -f or --foo and , for arrays
        line = re.sub(r'\b(\w)=\((.*?)\)', lambda m: f"-{m.group(1)},{process_array(m.group(2))}", line)
        line = re.sub(r'\b(\w)=', r'-\1=', line)
        line = re.sub(r'\b(\w\w+)=\((.*?)\)', lambda m: f"--{m.group(1)},{process_array(m.group(2))}", line)
        line = re.sub(r'\b(\w\w+)=', r'--\1=', line)

        # replace underscore with dashes, before any comment
        line = re.sub(r'_(?=[^#]*(#|$))', r'-', line)

        # tab before comment
        line = re.sub(r'(\S)(\s+)#', r'\1\t#', line)

        # Long and short options in separate columns
        if re.search(r'\s(-\w)', line):
            line = re.sub(r'\s(-\w)', r'\t\1', line)
        else:
            line = re.sub(r'\t', r'\t\t', line)

    logger.debug("  Processed line: %s", line)

    return line


def process_array(array_content: str) -> str:
    """Process the content of an array."""
    if ',' in array_content:
        return f'"{array_content}"'
    return array_content.replace(' ', ',')


def opts_help(
    put: geput.Put,
    script: str,
) -> None:
    """
    Generate a help message for command-line options based on the script's content.
    """

    script = Path(script)
    # while it's a symlink
    detect_loop = 0
    while script.is_symlink() and detect_loop < 10:
        if script.parent.name == "canon":
            break
        target = script.readlink()
        script = script.parent / target
        detect_loop += 1
    if detect_loop == 10:
        logger.error("Too many symlinks")
    script_name = script.name

    in_func = False
    blanks = 0
    skip_blank_lines = False

    lines = []

    def out(line=""):
        lines.append(line)

    out(f"{script_name} ")

    with open(script, "r") as istream:
        for line in istream:
            line = line.strip()

            # Skip shebang line
            if line.startswith('#!'):
                skip_blank_lines = True
                continue

            # Skip unindented function declaration
            if re.match(r'^[a-zA-Z0-9_-]+\(\)\s*\{', line):
                continue

            is_blank = len(line.strip()) == 0

            # Stop before the ". opts" line
            if re.match(r'\s*\.\s+opts', line):
                break

            # Stop before an eval line,
            # such as: eval "$(ally)"
            # which calls: . opts
            if re.search(r'\beval\s', line):
                break

            # Skip other ". " lines
            if re.match(r'\s*\.\s', line):
                continue

            # Skip shellcheck disable lines
            if re.match(r'\s*# shellcheck disable=', line):
                continue

            # Handle blank lines
            if is_blank:
                blanks += 1
                continue

            # Output a single blank line if needed
            if blanks > 0 and not skip_blank_lines:
                out("\n")
            blanks = 0
            skip_blank_lines = False

            # Process and output the line
            processed_line = process_line(line, script_name)
            out(processed_line + "\n")

    output = "".join(lines)

    try:
        # TODO use tsv2txt module directly
        output = sh.Command("tsv2txt")("-m", _in=output)
    except sh.CommandNotFound:
        logger.warning("tsv2txt not available, keeping lines unchanged")

    put(output)


def setup_args(parser: argparse.ArgumentParser) -> None:
    """Set up the command-line arguments."""
    parser.description = "Generate a help message for command-line options based on the script's content."
    parser.add_argument("script", help="Path to the script file")


if __name__ == "__main__":
    main.go(opts_help, setup_args)
