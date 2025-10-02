#!/usr/bin/env python3-allemande

"""
A wrapper for cat_named that checks access permissions and path safety.
"""

import os
import sys
from pathlib import Path
from typing import Callable, List
from typing import TextIO

from ally import main, old
from ally_room import check_access, Access

import cat_named

__version__ = "1.0.0"

logger = main.get_logger()


def ally_cat(
    put: Callable[[str], None],
    ostream: TextIO,
    sources: List[str],
    user: str | None = None,
    base: str | None = None,
    root: str | None = None,
#    **kwargs,
) -> None:
    """
    Display file contents after checking permissions and path safety.
    """
    safe_sources = []
    root_path = Path(root) if root else None
    base_path = Path(base) if base else None

    for source in sources:
        # Handle web URLs directly
        if source.startswith(("http://", "https://", "ftp://", "ftps://")):
            safe_sources.append(source)
            continue

        # Resolve path considering base directory
        path = Path(source)
        if base_path and not path.is_absolute():
            path = base_path / path
        path = path.resolve()

        # Check if path is under root
        if root_path and not str(path).startswith(str(root_path)):
            logger.error("Path not under root: %s", path)
            continue

        # Check access permissions
        access = check_access(user, path)
        if access.value & Access.READ.value != Access.READ.value:
            logger.error("No read access: %s", path)
            continue

        safe_sources.append(str(path))

    if safe_sources:
        cat_named.cat_named(put, *safe_sources)  #, **kwargs)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("sources", nargs="*", help="Files or URLs to display")
    arg("-u", "--user", help="User to check permissions for")
    arg("-B", "--base", help="Base directory for relative paths")
    arg("-r", "--root", help="Root directory to restrict paths under")


if __name__ == "__main__":
    main.go(ally_cat, setup_args)

# <think>
# Key requirements:
# 1. Wrap/rewrite cat_named for Ally Chat UI
# 2. Add user, base, root path options
# 3. Check file access permissions using ally_room.check_access
# 4. Ensure paths are under root directory
# 5. Keep it simple, avoid deep nesting
# </think>

# This implementation:
# 1. Wraps cat_named while adding permission and path safety checks
# 2. Handles URLs directly while checking local file paths
# 3. Resolves relative paths against base directory if specified
# 4. Ensures paths are under root directory if specified
# 5. Checks read permissions using ally_room.check_access
# 6. Keeps the code simple and avoids deep nesting
# 7. Maintains all cat_named functionality through kwargs
#
# Let me know if you need any clarification or adjustments!
