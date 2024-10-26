#!/usr/bin/env python3

"""
This module implements an indent-aware unified diff.
It understands indent structure to avoid mapping one function to multiple functions.
"""

import difflib
from dataclasses import dataclass, field
from typing import List, Optional

from ally import main, logs, geput  # type: ignore

__version__ = "0.1.8"

logger = logs.get_logger()


@dataclass
class Block:
    """Represents a block defined by its indentation level."""

    indent: int
    start: int
    end: Optional[int] = None
    lines: list[str] = field(default_factory=list)


def extract_blocks(lines: List[str]) -> List[Block]:
    """
    Extract blocks from the given lines based on indentation levels.

    Returns a list of Block instances.
    """
    blocks: List[Block] = []
    block_stack: List[Block] = []

    for lineno, line in enumerate(lines):
        stripped_line = line.rstrip("\n")
        if not stripped_line.strip():
            continue  # Skip empty lines

        indent = len(line) - len(line.lstrip(" \t"))

        if not block_stack:
            current_block = Block(indent=indent, start=lineno, lines=[line])
            block_stack.append(current_block)
            continue

        # Handle decreasing indentation
        while block_stack and indent < block_stack[-1].indent:
            finished_block = block_stack.pop()
            finished_block.end = lineno - 1
            blocks.append(finished_block)

        if block_stack and indent == block_stack[-1].indent:
            # Same level, continue current block
            block_stack[-1].lines.append(line)
        else:
            # Indentation increased or new block after popping all
            current_block = Block(indent=indent, start=lineno, lines=[line])
            block_stack.append(current_block)

    # Finish remaining blocks
    while block_stack:
        finished_block = block_stack.pop()
        finished_block.end = len(lines) - 1
        blocks.append(finished_block)

    return blocks


def compare_blocks(blocks1: List[Block], blocks2: List[Block]) -> List[str]:
    """
    Compare blocks from two files and generate a diff.

    Returns a list of diff lines.
    """
    diff = []
    seq1 = ["".join(block.lines) for block in blocks1]
    seq2 = ["".join(block.lines) for block in blocks2]
    sm = difflib.SequenceMatcher(None, seq1, seq2)

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        diff.extend(process_diff(tag, blocks1[i1:i2], blocks2[j1:j2]))

    return diff


def process_diff(tag: str, blocks1: List[Block], blocks2: List[Block]) -> List[str]:
    """Process a single diff operation."""
    if tag == "replace":
        return process_replace(blocks1, blocks2)
    if tag == "delete":
        return process_delete(blocks1)
    if tag == "insert":
        return process_insert(blocks2)
    return []


def process_replace(blocks1: List[Block], blocks2: List[Block]) -> List[str]:
    """Process a replace operation."""
    diff = []
    for block1, block2 in zip(blocks1, blocks2):
        block_diff = list(
            difflib.unified_diff(
                block1.lines,
                block2.lines,
                fromfile="file1",
                tofile="file2",
                lineterm="",
            )
        )
        if block_diff:
            diff.extend(block_diff)
            diff.append("")  # Add a newline after each block diff

    # Handle any extra unmatched blocks
    diff.extend(process_delete(blocks1[len(blocks2) :]))
    diff.extend(process_insert(blocks2[len(blocks1) :]))
    return diff


def process_delete(blocks: List[Block]) -> List[str]:
    """Process a delete operation."""
    diff = []
    for block in blocks:
        diff.append("--- file1")
        diff.append("+++ file2")
        diff.extend(f"-{line}" for line in block.lines)
        diff.append("")  # Add a newline after each block
    return diff


def process_insert(blocks: List[Block]) -> List[str]:
    """Process an insert operation."""
    diff = []
    for block in blocks:
        diff.append("--- file1")
        diff.append("+++ file2")
        diff.extend(f"+{line}" for line in block.lines)
        diff.append("")  # Add a newline after each block
    return diff


def diff_blocks(file1: str, file2: str) -> List[str]:
    """
    Generate an indent-aware unified diff between two files.
    """
    with open(file1, "r", encoding="utf-8") as f1, open(file2, "r", encoding="utf-8") as f2:
        lines1 = [l.rstrip() for l in f1.readlines()]
        lines2 = [l.rstrip() for l in f2.readlines()]

    blocks1 = extract_blocks(lines1)
    blocks2 = extract_blocks(lines2)

    diff = compare_blocks(blocks1, blocks2)

    return diff


def print_diff(diff: List[str], put: geput.Put) -> None:
    """Print the generated diff."""
    print = geput.print(put)
    for line in diff:
        print(line)


def main_diff(put: geput.Put, file1: str, file2: str) -> None:
    """Main function to generate and print the indent-aware diff."""
    diff = diff_blocks(file1, file2)
    print_diff(diff, put)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("file1", help="first file for comparison")
    arg("file2", help="second file for comparison")


if __name__ == "__main__":
    main.go(main_diff, setup_args)
