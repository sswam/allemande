#!/usr/bin/env python3

"""
This module splits a YAML or tree-indented file into sections based on character or line count,
duplicating context lines when it can't split at the top level.
"""

import os
import sys
import logging
from typing import TextIO, List
from pathlib import Path

from argh import arg

from ally import main
from ally.lazy import lazy
import aligno

__version__ = "0.1.2"

logger = main.get_logger()


def split_content(content: List[str], max_count: int, min_count: int, use_chars: bool) -> List[List[str]]:
    """Split the content into sections based on character or line count."""
    sections = []
    current_section = []
    current_count = 0
    context_lines = []

    indent_size, _, _ = aligno.detect_indent(content)

    for line in content:
        line_count = len(line) if use_chars else 1
        if current_count + line_count > max_count and (current_count >= min_count or not current_section):
            sections.append(current_section)
            current_section = [*context_lines]
            current_count = 0

        current_section.append(line)
        current_count += line_count

        # Calculate the indentation level of the current line
        indent = len(line) - len(line.lstrip()) // indent_length

        # Trim the context_lines to match the current indentation level
        context_lines = context_lines[:indent - 1]

        # Pad the context_lines with empty strings if needed and add the current line
        context_lines += [""] * (indent - len(context_lines)) + [line]

    if current_section:
        sections.append(current_section)

    return sections


@arg("-m", "--max", dest="max_count", type=int, help="maximum character/line count (default: 50000 chars or 800 lines)")
@arg("-n", "--min", dest="min_count", type=int, help="minimum character/line count (default: 50% of max)")
@arg("-c", "--chars", help="use character count instead of line count")
@arg("-f", "--force", help="overwrite existing files")
def indent_split(
    out_path: str = 'split.txt',
    max_count: int = None,
    min_count: int = None,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    chars: bool = False,
    force: bool = False,
) -> None:
    """
    Split a tree-indented file such as YAML or Python into sections based on character or line count.
    """
    get, _put = main.io(istream, ostream)

    if max_count is None:
        max_count = 50000 if chars else 800
    if min_count is None:
        min_count = max_count // 2

    content = get(chunks=True)
    sections = split_content(content, max_count, min_count, chars)

    out_dir = Path(out_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_stem, out_ext = os.path.splitext(out_path)

    for i, section in enumerate(sections, 1):
        file_path = f"{out_stem}_{i:06d}{out_ext}"

        mode = 'w' if force else 'x'

        try:
            with open(file_path, mode) as f:
                f.write("".join(section))
            logger.info(f"Wrote section {i} to {file_path}")
        except FileExistsError:
            logger.warning(f"File {file_path} already exists. Use --force to overwrite.")

    logger.info(f"Split into {len(sections)} sections")


if __name__ == "__main__":
    main.run(indent_split)
