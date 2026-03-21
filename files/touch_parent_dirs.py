#!/usr/bin/env python3-allemande

"""
Update mtime for each folder to the maximum of each child descendant's mtime, depth first.
"""

import os
import sys
from typing import TextIO
from pathlib import Path

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


def process_entry(entry: Path) -> float:
    if entry.name.startswith("."):
        return 0

    stat = entry.stat(follow_symlinks=False)
    atime = stat.st_atime
    mtime = stat.st_mtime

    if entry.is_symlink() or not entry.is_dir():
        return mtime

    # Recurse into directory
    max_child_mtime = 0
    for child in os.scandir(entry):
        child_mtime = process_entry(Path(child.path))
        max_child_mtime = max(max_child_mtime, child_mtime)

    # if max_child_mtime > mtime:
    if max_child_mtime > 0:
        # touch this entry with max_child_mtime
        if max_child_mtime != mtime:
            logger.debug("Updating mtime: %s %s", max_child_mtime, str(entry))
            os.utime(entry, times=(atime, max_child_mtime))
            mtime = max_child_mtime

    return mtime


def touch_parent_dirs(folder: str) -> None:
    process_entry(Path(folder))


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("folder", help="root folder to walk")


if __name__ == "__main__":
    main.go(touch_parent_dirs, setup_args)
