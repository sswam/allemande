#!/usr/bin/env python3-allemande

""" Ally Chat notifications """

import os
import sys
import argparse
import logging
from pathlib import Path
import re
import asyncio

from watchfiles import Change

import atail  # type: ignore
import ucm  # type: ignore
import tasks
import settings
import ally_notify


logger = logging.getLogger(__name__)
logging.getLogger('watchfiles').setLevel(logging.WARNING)


def text_mentions(text: str, user: str) -> bool:
    """
    Check if text mentions a user
    - look for @user (any case), preceded by \W or start, followed by \b
    - or User (title case), preceded by \b and followed by \b
    """
    if re.search(rf"(?:^|\W)@{re.escape(user)}\b", text, re.IGNORECASE):
        return True
    if re.search(rf"\b{re.escape(user.title())}\b", text):
        return True
    return False


async def file_changed(file_type, file_path, change_type, old_size, new_size):
    """Process a change to a file."""
    logger.info("change, old_size, new_size: %r, %r, %r", change_type, old_size, new_size)

    if change_type == Change.deleted:
        return
    if old_size and new_size < old_size:
        return
    if new_size == 0 and old_size != 0:
        return

    poke = file_type == "room" and new_size == old_size

    if poke:
        return

    old_size = old_size or 0

    path_rooms = str(settings.PATH_ROOMS)+"/"
    if not file_path.startswith(path_rooms):
        raise ValueError(f"file_changed: file_path is not under PATH_ROOMS: {file_path}")
    rel_path = file_path[len(path_rooms):]
    rel_path = re.sub(r"\.bb$", "", rel_path)  # to watch a room file XXX

    user_setting_list = ally_notify.notify_who(rel_path)
    logger.info("notify who for %s: %r", rel_path, user_setting_list)
    user_setting_list = [x for x in user_setting_list if x[1] != "off"]

    if not user_setting_list:
        return

    new_text = ""

    if file_type == "room" and any(x[1] == "me" for x in user_setting_list):
        with open(file_path, "rb") as f:
            f.seek(old_size or 0)
            raw_bytes = f.read(new_size - old_size)
        new_text = raw_bytes.decode("utf-8", errors='ignore')

    tasks = [
        ally_notify.notification_as_needed(user, rel_path)
        for user, setting in user_setting_list
        if setting == "all" or (setting == "me" and text_mentions(new_text, user))
    ]

    await asyncio.gather(*tasks)


LOCAL_AGENT_PATTERN = re.compile(r'^' + re.escape(str(settings.PATH_ROOMS)) + r'/.*?/agents/')

def check_file_type(path):
    """Check the file type, either room or agent."""
    ext = Path(path).suffix
    if ext == ".bb" and path.startswith(str(settings.PATH_ROOMS)+"/"):
        return "room"
    if ext == ".yml" and path.startswith(str(settings.PATH_ROOMS/"agents")+"/"):
        return "agent"
    if ext == ".yml" and LOCAL_AGENT_PATTERN.match(path):
        return "local_agent"
    return None


async def watch_loop(args):
    """Follow the watch log, and notify users."""

    async with atail.AsyncTail(filename=args.watch, follow=True, rewind=True) as queue:
        while (line := await queue.get()) is not None:
            try:
                file_path, change_type, old_size, new_size = line.rstrip("\n").split("\t")
                change_type = Change(int(change_type))
                old_size = int(old_size) if old_size != "" else None
                new_size = int(new_size) if new_size != "" else None

                file_type = check_file_type(file_path)

                logger.info("File change detected: %r, type: %r", file_path, file_type)

                if not os.access(file_path, os.W_OK):
                    logger.info("Ignoring change to unwritable file: %r", file_path)
                elif file_type:
                    task = asyncio.create_task(file_changed(file_type, file_path, change_type, old_size, new_size))
                    tasks.add_task(task, f"file changed: {file_path}")
                    tasks.list_active_tasks()
                else:
                    logger.debug("Ignoring change to file: %r", file_path)
            except Exception:  # pylint: disable=broad-except
                logger.exception("Error processing file change", exc_info=True)
            finally:
                queue.task_done()


def get_opts():  # pylint: disable=too-many-statements
    """Get the command line options."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument("--watch", "-w", default=None, help="Follow this watch log file")

    ucm.add_logging_options(parser)

    args = parser.parse_args()

    ucm.setup_logging(args)

    logger.debug("Options: %r", args)

    return args


async def main():
    """Main function."""
    args = get_opts()

    if not args.watch:
        raise ValueError("Watch file not specified")

    logger.info("Watching chat rooms")
    await watch_loop(args)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("interrupted")
        sys.exit(0)
