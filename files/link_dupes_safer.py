#!/usr/bin/env python3-allemande

"""
Creates hard links between duplicate files, preserving the first occurrence and linking others to it.

Usage:
    ... | link_dupes [--dry-run] [--backup]
"""

import os
import itertools
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.1"

logger = logs.get_logger()


def safe_hardlink(src: str, dst: str, dry_run: bool = False, backup: bool = False) -> bool:
    """Safely create a hard link, with verification."""
    # Verify both files exist
    if not os.path.exists(src):
        logger.error("Source file doesn't exist: %s", src)
        return False
    if not os.path.exists(dst):
        logger.error("Destination file doesn't exist: %s", dst)
        return False

    # Check if already hard-linked
    if os.path.samefile(src, dst):
        logger.info("SKIP: Already linked: %s", dst)
        return True

    # Verify same filesystem
    if os.stat(src).st_dev != os.stat(dst).st_dev:
        logger.error("Different filesystems: %s and %s", src, dst)
        return False

    # Verify files are actually identical
    if os.path.getsize(src) != os.path.getsize(dst):
        logger.error("Size mismatch: %s and %s", src, dst)
        return False

    if dry_run:
        logger.info("DRY-RUN: Would link %s -> %s", dst, src)
        return True

    if backup:
        # Create backup name
        backup_path = dst + ".backup-before-hardlink"

        # Rename original (don't delete!)
        os.rename(dst, backup_path)

        try:
            # Create hard link
            os.link(src, dst)
            # Success - remove backup
            os.unlink(backup_path)
            logger.info("SUCCESS: Linked %s -> %s", dst, src)
            return True
        except Exception as e:
            # Restore backup on failure
            os.rename(backup_path, dst)
            logger.error("Failed to link %s: %s", dst, e)
            return False
    else:
        # No backup - just replace directly
        try:
            # Remove destination
            os.unlink(dst)
            # Create hard link
            os.link(src, dst)
            logger.info("SUCCESS: Linked %s -> %s", dst, src)
            return True
        except Exception as e:
            logger.error("Failed to link %s: %s", dst, e)
            return False


def link_dupes(
    istream: TextIO,
    ostream: TextIO,
    dry_run: bool = False,
    backup: bool = False,
) -> None:
    """Process groups of duplicate files and link them."""
    for is_not_empty, files_group in itertools.groupby(istream, key=lambda x: bool(x.strip())):
        if not is_not_empty:
            continue

        files = [line.rstrip("\r\n") for line in files_group]
        if len(files) < 2:
            continue

        first_file = files[0]
        logger.info("Processing group: %s", first_file)

        for dup_file in files[1:]:
            safe_hardlink(first_file, dup_file, dry_run, backup)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("--dry-run", action="store_true", help="show what would be done")
    arg("--backup", action="store_true", help="create backup before linking")


if __name__ == "__main__":
    main.go(link_dupes, setup_args)
