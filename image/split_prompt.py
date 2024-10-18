#!/usr/bin/env python3

"""
Split a stable diffusion prompt into multiple lines, to be more readable.

Usage:
    echo "your prompt here" | python split_prompt.py
    python split_prompt.py < input_file.txt
"""

import sys
import re
import logging
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.1"

logger = logs.get_logger()


def split_prompt(prompt: str) -> str:
    result = []
    start = 0
    nesting = 0

    # Iterate through each character in the prompt
    for i, char in enumerate(prompt):
        # Track nesting level of parentheses
        if char == "(":
            nesting += 1
        elif char == ")":
            nesting -= 1
        # Split on commas, but only if not inside parentheses
        elif char == "," and nesting == 0:
            current = prompt[start : i + 1].strip()
            following = prompt[i + 1 :].strip()
            # Avoid splitting between consecutive score_X terms
            if not (re.match(r"score_\d", current) and re.match(r"score_\d", following)):
                result.append(current)
                start = i + 1

    # Add the last part of the prompt
    if start < len(prompt):
        result.append(prompt[start:].strip())

    # Join the split parts with newlines
    result = "\n".join(result)

    # Split on BREAK
    result = re.sub(r"\s*\b(BREAK)\b\s*", r"\n\n\1 ", result)

    # Split on LoRAs
    result = re.sub(r"\s*(<lora)", r"\n\1", result)

    return result


def process_input(istream: TextIO) -> None:
    """Process input from the given stream and print the split prompt."""
    prompt = istream.read()
    print(split_prompt(prompt).strip())


def setup_args(arg):
    """Set up the command-line arguments."""
    # none, yet


if __name__ == "__main__":
    main.go(process_input, setup_args)
