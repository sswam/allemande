#!/usr/bin/env python3-allemande

"""
Move files to numbered archive versions, finding the first unused number.
"""

from pathlib import Path
from typing import Callable
import re
import os

from ally import main, logs, bsearch  # type: ignore

__version__ = "0.1.2"

logger = logs.get_logger()


def path_for_num(path: Path, num: int) -> Path:
    """Create a numbered path, preserving any existing number in the stem."""
    stem = path.stem
    stem = re.sub(r'-\d+$', '', stem)
    return path.parent / f"{stem}-{num}{path.suffix}"


def find_unused_numbered_path(path: Path, number_path: Callable[[Path, int], Path] = path_for_num) -> Path:
    """Find the first unused number for a numbered path."""

    def is_unused(num: int) -> bool:
        return not number_path(path, num).exists()

    # Find first unused number using doubling+binary search
    first_unused = bsearch.find_lowest_int_true(is_unused, start=0)
    return number_path(path, first_unused)


def archive_file(path: Path) -> Path:
    """Archive a single file to the next available numbered version."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Not a regular file: {path}")

    if not os.access(path, os.W_OK):
        raise PermissionError(f"File is not writable: {path}")

    new_path = find_unused_numbered_path(path)

    logger.info("Moving %s to %s", path, new_path)
    path.rename(new_path)

    return new_path


def archive_with(path: Path, derived_ext: str = "html") -> Path:
    """Archive a single file to the next available numbered version."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not path.is_file():
        raise ValueError(f"Not a regular file: {path}")

    if not os.access(path, os.W_OK):
        raise PermissionError(f"File is not writable: {path}")

    new_path = find_unused_numbered_path(path)

    logger.info("Moving %s to %s", path, new_path)
    derived_old = path.with_suffix("." + derived_ext)
    if derived_old.exists():
        if not os.access(derived_old, os.W_OK):
            raise PermissionError(f"Derived file is not writable: {derived_old}")
        derived_new = new_path.with_suffix("." + derived_ext)
        derived_old.rename(derived_new)
    path.rename(new_path)

    return new_path


def archive(files: list[str] | None = None, derived_ext: str = "html") -> None:
    """Archive the given files to numbered versions."""
    if not files:
        return

    for filename in files:
        try:
            if derived_ext:
                print(archive_with(Path(filename), derived_ext))
            else:
                print(archive_file(Path(filename)))
        except (FileNotFoundError, ValueError, PermissionError) as e:
            logger.error("%s", e)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("files", nargs="*", help="files to archive")
    arg(
        "--derived-ext",
        "-D",
        help="extension for derived files to archive",
    )


if __name__ == "__main__":
    main.go(archive, setup_args)
