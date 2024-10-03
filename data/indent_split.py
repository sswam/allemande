#!/usr/bin/env python3

"""
This module splits a YAML or tree-indented file into sections based on character or line count,
duplicating context lines when it can't split at the top level.
"""

import os
import sys
import logging
import argparse
from typing import TextIO, List
from pathlib import Path

__version__ = "0.1.4"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_break_point(section: List[str]) -> int:
    """Find the least indented line within the range, preferring later lines for equal indentation."""
    min_indent = min(len(line) - len(line.lstrip()) for line in section)
    for i in range(len(section) - 1, -1, -1):
        if len(section[i]) - len(section[i].lstrip()) == min_indent:
            return i
    return len(section) - 1


def get_context_lines(content: List[str], index: int) -> List[str]:
    """Get context lines for the given index."""
    context = []
    current_indent = None
    for line in reversed(content[:index]):
        indent = len(line) - len(line.lstrip())
        if current_indent is None or indent < current_indent:
            context.insert(0, line)
            current_indent = indent
        if indent == 0:
            break
    return context


def split_content(
    content: List[str], max_count: int, min_count: int, use_chars: bool
) -> List[List[str]]:
    """Split the content into sections based on character or line count."""
    sections = []
    current_section = []
    current_count = 0

    for i, line in enumerate(content):
        line_count = len(line) if use_chars else 1
        if current_count + line_count > max_count and current_count >= min_count:
            break_point = find_break_point(current_section)
            sections.append(
                get_context_lines(content, i - len(current_section))
                + current_section[: break_point + 1]
            )
            current_section = current_section[break_point + 1 :]
            current_count = sum(len(l) if use_chars else 1 for l in current_section)

        current_section.append(line)
        current_count += line_count

    if current_section:
        sections.append(
            get_context_lines(content, len(content) - len(current_section))
            + current_section
        )

    return sections


def indent_split(
    out_path: str = "split.txt",
    max_count: int = None,
    min_count: int = None,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    chars: bool = False,
    force: bool = False,
    equal: bool = False,
    number: int = None,
) -> None:
    """
    Split a tree-indented file such as YAML or Python into sections based on character or line count.
    """
    content = istream.readlines()
    total_count = sum(len(line) if chars else 1 for line in content)

    if number:
        max_count = total_count // number
    elif equal:
        max_count = total_count // (
            total_count // (max_count or (50000 if chars else 800))
        )
    elif max_count is None:
        max_count = 50000 if chars else 800

    if min_count is None:
        min_count = max_count // 2

    sections = split_content(content, max_count, min_count, chars)

    if any(
        sum(len(line) if chars else 1 for line in section) < min_count
        for section in sections[:-1]
    ):
        logger.error("Failed to meet minimum count requirement for all sections.")
        sys.exit(1)

    out_dir = Path(out_path).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    out_stem, out_ext = os.path.splitext(out_path)

    for i, section in enumerate(sections, 1):
        file_path = f"{out_stem}_{i:06d}{out_ext}"

        mode = "w" if force else "x"

        try:
            with open(file_path, mode) as f:
                f.write("".join(section))
            logger.info(f"Wrote section {i} to {file_path}")
        except FileExistsError:
            logger.warning(
                f"File {file_path} already exists. Use --force to overwrite."
            )

    logger.info(f"Split into {len(sections)} sections")

def main():
    parser = argparse.ArgumentParser(description="Split a tree-indented file into sections.")
    parser.add_argument("out_path", nargs="?", default="split.txt", help="Output path")
    parser.add_argument("-m", "--max", dest="max_count", type=int, help="Maximum character/line count")
    parser.add_argument("-n", "--min", dest="min_count", type=int, help="Minimum character/line count")
    parser.add_argument("-c", "--chars", action="store_true", help="Use character count instead of line count")
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing files")
    parser.add_argument("-e", "--equal", action="store_true", help="Recalculate max for equal-sized chunks")
    parser.add_argument("-N", "--number", type=int, help="Specify the number of output files")

    args = parser.parse_args()

    indent_split(
        out_path=args.out_path,
        max_count=args.max_count,
        min_count=args.min_count,
        chars=args.chars,
        force=args.force,
        equal=args.equal,
        number=args.number
    )

if __name__ == "__main__":
    main()
