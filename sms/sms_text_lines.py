#!/usr/bin/env python3-allemande

"""
This script parses SMS conversation text from input like fallon.txt and outputs each message as a single TSV line.
Fields: Type, Date, Name/Number, Content
Where Date includes the time.
"""

import re
from typing import TextIO

from ally import main  # type: ignore

__version__ = "0.1.1"


def collect_messages(lines: list[str]) -> list[tuple[str, str, str, str]]:
    """Collect and parse message blocks from the input lines."""
    messages = []
    current_block = []
    in_block = False
    for line in lines:
        if line == "Sent" or line == "Received":
            if current_block:
                msg = parse_message(current_block)
                if msg:
                    messages.append(msg)
            current_block = [line]
            in_block = True
        elif in_block:
            current_block.append(line)
    if current_block:
        msg = parse_message(current_block)
        if msg:
            messages.append(msg)
    return messages


def parse_message(block: list[str]) -> tuple[str, str, str, str] | None:
    """Parse a single message block into type, full_date, name_number, content."""
    if not block:
        return None
    type_ = block[0]
    idx = 1
    if type_ == "Received":
        if idx < len(block) and block[idx] == "Sent by:":
            idx += 1
            # Skip the name part until date
            while idx < len(block) and not re.match(r'\d{1,2} \w+ \d{4}', block[idx]):
                idx += 1
        # Now idx should be at date
        if idx >= len(block):
            return None
        date = block[idx]
        idx += 1
        if idx >= len(block):
            return None
        time = block[idx]
        idx += 1
        if idx >= len(block):
            return None
        name_number = block[idx]
        idx += 1
        content = ' '.join(block[idx:]).strip()
    elif type_ == "Sent":
        if idx >= len(block):
            return None
        date = block[idx]
        idx += 1
        if idx >= len(block):
            return None
        time = block[idx]
        idx += 1
        if idx >= len(block):
            return None
        name_number = block[idx]
        idx += 1
        content = ' '.join(block[idx:]).strip()
    else:
        return None
    full_date = f"{date} {time}".strip()
    return type_, full_date, name_number, content


def sms_text_lines(istream: TextIO, ostream: TextIO) -> None:
    """Parse input and output messages as TSV lines."""
    lines = [line.rstrip() for line in istream]
    messages = collect_messages(lines)
    for msg in messages:
        ostream.write('\t'.join(msg) + '\n')


if __name__ == "__main__":
    main.go(sms_text_lines)
