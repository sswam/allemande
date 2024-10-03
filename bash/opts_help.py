#!/usr/bin/env python3

"""
This module generates a help message for command-line options based on the script's content.
"""

import os
import sys
import re
import textwrap
from typing import TextIO

import sh

from ally import main

__version__ = "0.1.1"

logger = main.get_logger()


def process_line(line: str, script_name: str) -> str:
    """Process a single line of the script."""
    # Remove indent
    line = line.lstrip()

    # Remove 'local ' from start of line
    line = re.sub(r'^local\s+', '', line)

    # Replace literal '$0' in lines with the value of script_name
    line = line.replace('$0 ', f'{script_name} ')

    if re.match(r'#\s*', line):
        # Remove '#' from the line
        line = re.sub(r'^#\s*', '', line)
    else:
        # Add dashes for -f or --foo and , for arrays
        line = re.sub(r'\b(\w)=\((.*?)\)', lambda m: f"-{m.group(1)},{process_array(m.group(2))}", line)
        line = re.sub(r'\b(\w)=', r'-\1=', line)
        line = re.sub(r'\b(\w\w+)=\((.*?)\)', lambda m: f"--{m.group(1)},{process_array(m.group(2))}", line)
        line = re.sub(r'\b(\w\w+)=', r'--\1=', line)

        # Long and short options in separate columns
        line = re.sub(r' (-\w)', r'\t\1', line)
        if not re.search(r'\t.*?\t', line):
            line = re.sub(r'\t', r'\t\t', line)

    return line


def process_array(array_content: str) -> str:
    """Process the content of an array."""
    if ',' in array_content:
        return f'"{array_content}"'
    return array_content.replace(' ', ',')


def opts_help(script, istream: TextIO = sys.stdin, ostream: TextIO = sys.stdout) -> None:
    """
    Generate a help message for command-line options based on the script's content.
    """
    _get, put = main.io(istream, ostream)

    script_name = os.path.basename(script)

    lines = []
    lines.append(f"{script_name} ")

    in_func = False
    blanks = 0
    skip_blank_lines = False

    with open(script, "r") as istream:
        for line in istream:
            line = line.rstrip()

            # Skip shebang line
            if line.startswith('#!'):
                skip_blank_lines = True
                continue

            # Skip unindented function declaration
            if re.match(r'^[a-zA-Z0-9_]+\(\)\s*\{', line):
                continue

            is_blank = len(line.strip()) == 0

            # Stop before the ". opts" line
            if re.match(r'\s*\.\s+opts', line):
                break

            # Stop before an eval line,
            # such as: eval "$(ally)"
            # which calls: . opts
            if re.match(r'\s*eval\s', line):
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
                lines.append("\n")
            blanks = 0
            skip_blank_lines = False

            # Process and output the line
            processed_line = process_line(line, script_name)
            lines.append(processed_line + "\n")

    text = "".join(lines)

    try:
        # TODO use tsv2txt module directly
        text = sh.tsv2txt("-m", _in=text)
    except sh.CommandNotFound:
        pass  # tsv2txt not available, keep lines unchanged

    put(text)


if __name__ == "__main__":
    main.run(opts_help)
