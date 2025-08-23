#!/usr/bin/env python3-allemande

"""
Extract names and @mentions from text. Names are sequences of 1-4 words, first and last must be capitalized.
@mentions can include lowercase and match greedily up to 4 words.
"""

import regex
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.2"

logger = logs.get_logger()

# Match 1-4 words where first and last are capitalized, or @mentions of 1-4 words
NAME_PATTERN = regex.compile(
    r"""
    (?:
        # Names: 1-4 words, first and last must be capitalized
        [A-Z0-9][\w\-\.']*                      # First word must be capitalized
        (?:\s+[\w\-\.']+){0,2}                  # Optional middle words (0-2)
        (?:\s+[A-Z0-9][\w\-\.']*)?             # Optional last word must be capitalized if present
        |
        # @mentions: @ followed by 1-4 words
        @[\w\-\.']+(?:\s+[\w\-\.']+){0,3}
    )
    """,
    regex.VERBOSE | regex.UNICODE,
)


def extract_partial_names(text: str) -> list[str]:
    """Extract all possible subsequences of consecutive words from a multi-word string."""
    words = text.split()
    names = []

    start = 0
    for end in range(start + 1, len(words) + 1):
        name = ' '.join(words[start:end])
        names.append(name)

    return names


def extract_names(
    istream: TextIO,
    ostream: TextIO,
) -> None:
    """Extract names and @mentions from input text."""
    text = istream.read()
    matches = NAME_PATTERN.finditer(text, overlapped=True)

    results = list()
    for match in matches:
        name = match.group().strip()
        results += extract_partial_names(name)

    for name in results:
        ostream.write(f"{name}\n")


def setup_args(arg):
    """Set up command-line arguments."""


if __name__ == "__main__":
    main.go(extract_names, setup_args)
