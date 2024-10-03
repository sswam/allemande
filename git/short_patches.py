#!/usr/bin/env python3

"""
This module sorts git diff output with multiple files from shortest patch to longest.
"""

import sys
import logging
from typing import TextIO
from collections import defaultdict

from argh import arg

from ally import main

__version__ = "0.1.0"

logger = main.get_logger()


def parse_git_diff(diff_output: str) -> dict[str, list[str]]:
    """Parse git diff output and group patches by filename."""
    patches = defaultdict(list)
    current_file = None

    for line in diff_output.splitlines():
        if line.startswith("diff --git"):
            current_file = line.split()[-1].lstrip("b/")
        elif current_file is not None:
            patches[current_file].append(line)

    return patches


def sort_patches_by_length(patches: dict[str, list[str]]) -> list[tuple[str, list[str]]]:
    """Sort patches by length, from shortest to longest."""
    return sorted(patches.items(), key=lambda x: len(x[1]))


def format_sorted_patches(sorted_patches: list[tuple[str, list[str]]]) -> str:
    """Format sorted patches for output."""
    output = []
    for filename, patch_lines in sorted_patches:
        output.append(f"diff --git a/{filename} b/{filename}")
        output.extend(patch_lines)
        output.append("")  # Add a blank line between patches
    return "\n".join(output)


@arg("--reverse", help="sort from longest to shortest")
def short_patches(
    *filenames: str,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    reverse: bool = False,
) -> None:
    """
    Sort git diff output with multiple files from shortest patch to longest.
    """
    get, put = main.io(istream, ostream)

    if filenames:
        logger.warning("Ignoring provided filenames. Reading from stdin.")

    diff_output = get(all=True)

    if not diff_output:
        logger.info("No input provided. Exiting.")
        return

    patches = parse_git_diff(diff_output)
    sorted_patches = sort_patches_by_length(patches)

    if reverse:
        sorted_patches.reverse()

    formatted_output = format_sorted_patches(sorted_patches)
    put(formatted_output)


if __name__ == "__main__":
    main.run(short_patches)
