#!/usr/bin/env python3

"""
This module deduplicates files by hardlinking, symlinking, or calculating space savings.
"""

import os
import logging
from collections import defaultdict
from typing import TextIO

from ally import main, logs

__version__ = "0.1.1"

logger = logs.get_logger()


def calculate_space_savings(dupes: dict[str, list[str]]) -> int:
    """Calculate the amount of space that will be saved by deduplication."""
    total_savings = 0
    for files in dupes.values():
        if len(files) > 1:
            file_size = os.path.getsize(files[0])
            total_savings += file_size * (len(files) - 1)
    return total_savings


def create_hardlinks(dupes: dict[str, list[str]]) -> None:
    """Create hardlinks for duplicate files."""
    for files in dupes.values():
        if len(files) > 1:
            source = files[0]
            for duplicate in files[1:]:
                os.remove(duplicate)
                os.link(source, duplicate)
                logger.info("Created hardlink: %s -> %s", source, duplicate)


def create_symlinks(dupes: dict[str, list[str]]) -> None:
    """Create symlinks for duplicate files."""
    for files in dupes.values():
        if len(files) > 1:
            source = files[0]
            for duplicate in files[1:]:
                os.remove(duplicate)
                os.symlink(source, duplicate)
                logger.info("Created symlink: %s -> %s", source, duplicate)


def dedup(
    istream: TextIO,
    ostream: TextIO,
    checksum: bool = False,
    hardlink: bool = False,
    symlink: bool = False,
) -> None:
    """
    Deduplicate files based on input from stdin.
    By default, it calculates and shows space savings.
    """
    dupes = defaultdict(list)

    for line in istream:
        line = line.strip()
        if checksum:
            the_checksum, filepath = line.split(None, 1)
            dupes[the_checksum].append(filepath)
        else:
            filepath = line
            dupes[filepath].append(filepath)
            for dup_line in istream:
                dup_line = dup_line.strip()
                if not dup_line:
                    break
                dupes[filepath].append(dup_line.strip())

    if hardlink:
        create_hardlinks(dupes)
        logger.info("Hardlinks created for duplicate files.")
    elif symlink:
        create_symlinks(dupes)
        logger.info("Symlinks created for duplicate files.")

    savings = calculate_space_savings(dupes)
    print(savings, file=ostream)


def setup_args(arg, parser) -> None:
    """Set up the command-line arguments."""
    arg("-c", "--checksum", action="store_true", help="expect checksum format rather than fdupes format")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-l", "--hardlink", action="store_true", help="create hardlinks for duplicate files")
    group.add_argument("-s", "--symlink", action="store_true", help="create symlinks for duplicate files")


if __name__ == "__main__":
    main.go(dedup, setup_args)
