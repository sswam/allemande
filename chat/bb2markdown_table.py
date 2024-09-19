#!/usr/bin/env python3

"""
bb2markdown.py - convert chat.bb format to markdown with tables

Usage:
    python bb2markdown.py < input.bb > output.md

This script may also be used as a module:
    from bb2markdown import convert_bb_to_markdown
"""

import sys
import logging
from typing import TextIO, List, Tuple

from argh import arg

from ally import main

__version__ = "1.0.0"

logger = main.get_logger()


def parse_bb_line(line: str) -> Tuple[str, str]:
    """Parse a line from the chat.bb format."""
    parts = line.split("\t", 1)
    if len(parts) == 2:
        return parts[0].rstrip(":"), parts[1].strip()
    return "", parts[0].strip()


def format_markdown_table(entries: List[Tuple[str, str]], paragraphs: bool) -> List[str]:
    """Format the parsed entries into a Markdown table."""
    table = ["| person | message |", "|----------|----------|"]
    for person, message in entries:
        if "\n\n" in message:
            if paragraphs:
                message = "<p>" + message.replace("\n\n", "</p><p>") + "</p>"
            message = message.replace("\n", "<br>")
        table.append(f"| {person} | {message} |")
    return table


def convert_bb_to_markdown(input: TextIO, output: TextIO, paragraphs: bool) -> None:
    """Convert chat.bb format to chat-table.md format."""
    entries = []
    current_person = ""
    current_message = ""

    for line in input:
        person, message = parse_bb_line(line)
        if person:
            if current_person:
                entries.append((current_person, current_message.strip()))
            current_person = person
            current_message = message
        else:
            current_message += f"\n{message}"

    if current_person:
        entries.append((current_person, current_message.strip()))

    markdown_table = format_markdown_table(entries, paragraphs)
    output.write("\n".join(markdown_table) + "\n")


@arg("--input", help="input file (default: stdin)")
@arg("--output", help="output file (default: stdout)")
@arg("--paragraphs", help="use HTML <p> tags instead of <br> tags")
def bb2markdown(
    input: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    paragraphs: bool = False,
) -> None:
    """
    Convert chat.bb format to chat-table.md format.
    """
    get, put = main.io(input, output)
    convert_bb_to_markdown(input, output, paragraphs)


if __name__ == "__main__":
    main.run(bb2markdown)
