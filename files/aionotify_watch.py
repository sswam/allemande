#!/usr/bin/env python3-allemande

"""
This module demonstrates a simple async file watcher using aionotify.
It watches a directory for file system events like create, delete, and modify.
"""

import asyncio
import sys
from pathlib import Path
from typing import TextIO

import aionotify  # type: ignore

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


async def watch_directory(
    directory: str,
) -> None:
    """Watch a directory for file system events asynchronously."""
    watcher = aionotify.Watcher()
    watcher.watch(
        directory,
        aionotify.Flags.CREATE
        | aionotify.Flags.DELETE
        | aionotify.Flags.MODIFY
        | aionotify.Flags.MOVED_FROM
        | aionotify.Flags.MOVED_TO,
    )
    await watcher.setup(asyncio.get_event_loop())

    logger.info("Watching directory: %s", directory)
    try:
        while True:
            event = await watcher.get_event()
            if event:
                print(f"{event.flags}\t{event.name or ''}")
    except asyncio.CancelledError:
        logger.info("Watcher stopped")
    finally:
        watcher.close()


def aionotify_watch(
    directory: str = ".",
) -> None:
    """Watch a directory for file system events."""
    if not Path(directory).is_dir():
        raise ValueError(f"Directory does not exist: {directory}")

    asyncio.run(watch_directory(directory))


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("directory", help="directory to watch (default: current)")


if __name__ == "__main__":
    main.go(aionotify_watch, setup_args)
