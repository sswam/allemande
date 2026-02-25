#!/usr/bin/env python3-allemande

"""
Extract names and @mentions from text. Names are sequences of 1-4 words, first and last must be capitalized.
@mentions can include lowercase and match greedily up to 4 words.
"""

import regex  # type: ignore[import]
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.3"

logger = logs.get_logger()

# Match 1-4 words where first and last are capitalized, or @mentions of 1-4 words
NAME_PATTERN = regex.compile(
    r"""
    (?:
        # Names: 1-4 words, first and last must be capitalized
        [A-Z0-9][\w\-\.']*          # First word must be capitalized
        (
            (                           # Optional middle words (0-2), excluding common stop words
                (?!and|or|with|the|a|an|in|on|for|to|by|at|from|is|it|as|but|if|nor|so|yet|then|after|before)
                (?:\s+[\w\-\.']+)
            ){0,2}
            (?:\s+[A-Z0-9][\w\-\.']*)   # Last word must be capitalized
        )?
        |
        # @mentions: @ followed by 1-4 words
        @[\w\-\.']+(?:\s+[\w\-\.']+){0,3}
    )
    """,
    regex.VERBOSE | regex.UNICODE,  # type: ignore[attr-defined]
)


NAME_PATTERN_AT_ONLY = regex.compile(
    r"""
        # @mentions: @ followed by 1-4 words
        @[\w\-\.']+(?:\s+[\w\-\.']+){0,3}
    """,
    regex.VERBOSE | regex.UNICODE,  # type: ignore[attr-defined]
)


def strip_possessive(name: str) -> str:
    """Strip trailing possessive 's or ' from a name."""
    if name.endswith("'s"):
        return name[:-2]
    if name.endswith("'"):
        return name[:-1]
    return name


def extract_partial_names(text: str) -> list[str]:
    """Extract all possible subsequences of consecutive words from a multi-word string. Strip off trailing punctuation."""
    words = text.split()
    names = []

    start = 0
    for end in range(start + 1, len(words) + 1):
        name = ' '.join(words[start:end])

        # Strip trailing punctuation
        name = regex.sub(r"[-.'_]+$", "", name)
        name = strip_possessive(name)
        names.append(name)

    return names


def extract_names(
    text: str,
    at_only: bool=False,
) -> list[str]:
    """Extract names and @mentions from input text."""
    pattern = NAME_PATTERN_AT_ONLY if at_only else NAME_PATTERN
    matches = pattern.finditer(text, overlapped=True)

    results = list()
    for match in matches:
        name = match.group().strip().lstrip("@")
        results += extract_partial_names(name)

    return results


def extract_names_cli(
    istream: TextIO,
    ostream: TextIO,
) -> None:
    """Extract names and @mentions from input text."""
    text = istream.read()
    results = extract_names(text)
    for name in results:
        ostream.write(f"{name}\n")


def setup_args(arg):
    """Set up command-line arguments."""


if __name__ == "__main__":
    main.go(extract_names_cli, setup_args)
