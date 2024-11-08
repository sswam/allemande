#!/usr/bin/env python3-allemande

"""
This module fixes patch line counts in diff files.
It reads from stdin, updates the @@ headers with correct line counts,
and writes the corrected patch to stdout.
"""

import sys
import re
import argparse
from typing import TextIO, Match

from ally import main

__version__ = "0.1.1"

logger = main.get_logger()


def update_chunk_header(match: Match[str]) -> str:
    """Update the chunk header with correct line counts."""
    old_start, old_count, new_start, new_count = map(int, match.groups())
    return f"@@ -{old_start},{old_count} +{new_start},{new_count} @@"


def process_patch(istream: TextIO, ostream: TextIO) -> None:
    """Process the patch, updating line counts in chunk headers."""
    chunk_pattern = re.compile(r"@@ -(\d+),(\d+) \+(\d+),(\d+) @@")
    current_chunk: list[str] = []
    old_lines = new_lines = 0
    chunk_match: Match[str] | None = None

    for line in istream:
        if line.startswith("@@"):
            if current_chunk:
                if chunk_match:
                    header = update_chunk_header(chunk_match)
                    ostream.write(f"{header}\n")
                    ostream.writelines(current_chunk)
                current_chunk = []
                old_lines = new_lines = 0

            chunk_match = chunk_pattern.match(line)
            if not chunk_match:
                logger.warning(f"Invalid chunk header: {line.strip()}")
                ostream.write(line)
                continue

        elif line.startswith("-"):
            old_lines += 1
        elif line.startswith("+"):
            new_lines += 1
        elif not line.startswith("\\"):
            old_lines += 1
            new_lines += 1

        current_chunk.append(line)

    if current_chunk and chunk_match:
        header = update_chunk_header(chunk_match)
        ostream.write(f"{header}\n")
        ostream.writelines(current_chunk)


def patch_fixer(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Fix patch line counts in diff files.
    Reads from stdin and writes to stdout.
    """
    process_patch(istream, ostream)


def setup_args(parser: argparse.ArgumentParser) -> None:
    """Set up the command-line arguments."""
    parser.description = "Fix patch line counts in diff files."


if __name__ == "__main__":
    main.go(patch_fixer, setup_args)
