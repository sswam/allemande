#!/usr/bin/env python3-allemande

""" Allemande utilities """

import logging
import os
import subprocess
from pathlib import Path
import re
from typing import Any

from starlette.exceptions import HTTPException

from settings import ROOM_MAX_DEPTH, ROOM_PATH_MAX_LENGTH


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def uniqo(l: list[Any]) -> list[Any]:
    """remove duplicates from a list while preserving order"""
    return list(dict.fromkeys(l))


class Symbol:  # pylint: disable=too-few-public-methods
    """A symbol singleton object"""

    def __init__(self, name):
        """Create a new symbol with the given name"""
        self.name = name

    def __repr__(self):
        """Return a string representation of the symbol"""
        return f"<{self.name}>"


def backup_file(path: str):
    """Backup a file using git.

    Args:
        path: Path to the file to backup (can be relative or absolute)

    Raises:
        subprocess.CalledProcessError: If git commands fail
        ValueError: If the file is not in a git repository
    """
    # Convert to absolute path
    abs_path = os.path.abspath(path)

    if not os.path.exists(abs_path):
        return

    logger.warning("backup_file: %s", path)
    logger.warning("  abs_path: %s", abs_path)

    # Find the git repo root directory
    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"], cwd=os.path.dirname(abs_path), text=True
        ).strip()
    except subprocess.CalledProcessError as exc:
        raise ValueError(f"File {path} is not in a git repository") from exc

    logger.warning("  repo_root: %s", repo_root)

    # Get path relative to repo root
    rel_path = os.path.relpath(abs_path, repo_root)

    logger.warning("  rel_path: %s", rel_path)

    # Run git commands from repo root
    try:
        subprocess.run(["git", "add", rel_path], check=True, cwd=repo_root)
        # Check if there are staged changes for the file
        result = subprocess.run(["git", "diff", "--staged", "--quiet", rel_path], cwd=repo_root, capture_output=True)

        # If exit code is 1, there are changes to commit
        if result.returncode == 1:
            # Proceed with commit
            subprocess.run(["git", "commit", "-m", f"Backup {rel_path}", rel_path], check=True, cwd=repo_root)
    except subprocess.CalledProcessError as e:
        # Handle any git command failures
        print(f"Git operation failed: {e}")


def tree_prune(tree: dict) -> dict:
    """Prune a tree in-place, removing None values."""
    for key, value in list(tree.items()):
        if value is None:
            del tree[key]
        elif isinstance(value, dict):
            tree_prune(value)
    return tree


# pylint: disable=too-many-locals
def tac(file, chunk_size=4096, binary=False, keepends=False):
    """Read a file in reverse, a line at a time."""
    with open(file, "rb") as f:
        # Seek to end of file
        f.seek(0, 2)
        # Get total file size
        total_size = remaining_size = f.tell()
        pos = total_size
        block = b""
        while remaining_size > 0:
            # Calculate size to read, limited by chunk_size
            read_size = min(chunk_size, remaining_size)
            # Move position back by read_size
            pos -= read_size
            f.seek(pos)
            # Read chunk and combine with previous block
            chunk = f.read(read_size)
            current = chunk + block
            # Split off any partial line at the start
            parts = current.split(b"\n", 1)
            if len(parts) > 1:
                parts[0] += b"\n"
                lines_text = parts[1]
                if not binary:
                    lines_text = lines_text.decode()
                lines = lines_text.splitlines(keepends=keepends)
                # Yield complete lines in reverse
                yield from reversed(lines)
            block = parts[0]
            remaining_size -= read_size
        # Yield final remaining text
        if block:
            if not binary:
                block = block.decode()
            yield block


def safe_join(base_dir: Path | str, *paths: str | Path) -> Path:
    """
    Return a safe path under base_dir, or raise ValueError if the path is unsafe.
    Preserves symlinks and only checks for path traversal attacks.
    Does not preserve trailing slash as Path can't do that, client should do that as needed.

    Args:
        base_dir: Base directory path
        *paths: Additional path components to join

    Returns:
        Path: Safe joined path

    Raises:
        ValueError: If resulting path would be outside base_dir
    """
    # Convert base_dir to Path if it's a string
    base_dir = Path(base_dir).absolute()

    # Convert all path components to strings and join them
    path_parts = [str(p) for p in paths]

    # Create complete path without resolving
    full_path = base_dir.joinpath(*path_parts)

    # Normalize the path (remove . and .., but don't resolve symlinks)
    normalized_path = Path(os.path.normpath(str(full_path)))
    normalized_base = Path(os.path.normpath(str(base_dir)))

    # Check if the normalized path starts with the normalized base path
    normalized_path_s = str(normalized_path)
    normalized_base_s = str(normalized_base)
    if not (normalized_path_s == normalized_base_s or normalized_path_s.startswith(normalized_base_s + os.sep)):
        raise ValueError(f"Path {full_path} is outside base directory {base_dir}")

    # Make sure they share the same root
    if normalized_path.root != normalized_base.root:
        raise ValueError(f"Path {full_path} is outside base directory {base_dir}")

    return full_path


def sanitize_filename(filename):
    """Sanitize a filename, allowing most characters."""

    assert isinstance(filename, str)
    assert "/" not in filename

    # remove leading dots and whitespace:
    # don't want hidden files
    filename = re.sub(r"^[.\s]+", "", filename)

    # remove trailing dots and whitespace:
    # don't want confusion around file extensions
    filename = re.sub(r"[.\s]+$", "", filename)

    # squeeze whitespace
    filename = re.sub(r"\s+", " ", filename)

    return filename


def sanitize_pathname(room):
    """Sanitize a pathname, allowing most characters."""

    if room in ("", "/"):
        return room

    is_dir = room.endswith("/")
    if is_dir:
        room = room[:-1]

    # split into parts
    parts = room.split("/")

    # sanitize each part
    parts = map(sanitize_filename, parts)

    # remove empty parts
    parts = list(filter(lambda x: x, parts))

    if not parts:
        raise HTTPException(status_code=400, detail="Please enter the name of a room.")

    # Check max depth BEFORE joining
    if len(parts) > ROOM_MAX_DEPTH:
        raise HTTPException(status_code=400, detail=f"The room is too deeply nested, max {ROOM_MAX_DEPTH} parts.")

    # join back together
    room = "/".join(parts)

    if len(room) > ROOM_PATH_MAX_LENGTH:
        raise HTTPException(status_code=400, detail=f"The room name is too long, max {ROOM_PATH_MAX_LENGTH} characters.")

    # check for control characters
    if re.search(r"[\x00-\x1F\x7F]", room):
        raise HTTPException(status_code=400, detail="The room name cannot contain control characters.")

    if is_dir:
        room += "/"

    return room
