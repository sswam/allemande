#!/usr/bin/env python3

"""
This module splits a YAML or tree-indented file into sections based on line count,
duplicating context lines when it can't split at the top level.
"""

import os
import sys
import logging
from typing import TextIO
from pathlib import Path

from argh import arg

from ally import main
from ally.lazy import lazy

__version__ = "0.1.1"

logger = main.get_logger()


def split_content(content: list[str], max_count: int, min_count: int) -> list[list[str]]:
    """Split the content into sections based on line count."""
    sections = []
    current_section = []
    current_count = 0
    context_lines = []

    for line in content:
        if current_count + 1 > max_count and current_count >= min_count:
            sections.append(context_lines + current_section)
            current_section = []
            current_count = 0

        current_section.append(line)
        current_count += 1

        indent = len(line) - len(line.lstrip())
        if indent == 0:
            context_lines = [line]
        elif indent <= 4:
            context_lines = context_lines[:1] + [line]

    if current_section:
        sections.append(context_lines + current_section)

    return sections


@arg("-m", "--max", type=int, help="maximum line count (default: 800 lines)")
@arg("-n", "--min", type=int, help="minimum line count (default: 50% of max)")
@arg("-f", "--force", help="overwrite existing files")
def indent_split(
    out_path: str = 'split.txt',
    max: int = None,
    min: int = None,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    force: bool = False,
) -> None:
    """
    Split a tree-indented file such as YAML or Python into sections based on line count.
    """
    get, _put = main.io(istream, ostream)

    if max is None:
        max = 800
    if min is None:
        min = max // 2

    content = get(all=True)
    sections = split_content(content, max, min)

    out_dir = Path(out_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_stem, out_ext = os.path.splitext(out_path)

    for i, section in enumerate(sections):
        file_path = f"{out_stem}_{i:06d}{out_ext}"

        mode = 'w' if force else 'x'

        with open(file_path, mode) as f:
            f.writelines(section)

        logger.info(f"Wrote section {i} to {file_path}")

    logger.info(f"Split into {len(sections)} sections")


if __name__ == "__main__":
    main.run(indent_split)
