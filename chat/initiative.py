#!/usr/bin/env python3-allemande

"""
Send a System message to a chat room, to prompt an AI to message a user at a certain time

Example use, from crontab:

0 * * * * /home/sam/allemande/chat/initiative.py -i 1800 -r 28800 -w 600 sam Ally Sam

This will prompt the AI agent Ally to talk to the user Sam in the chat room
sam.bb each hour, if they have not been chatting recently. It will wait for a
random time up to 10 minutes before sending the message, and will check that
the agent and user have not been chatting within the last half hour. If the
user did not respond last time, it will wait 8 hours before sending another.
"""

from datetime import datetime
import os
from pathlib import Path
import re
import time
import random

from ally import main, logs  # type: ignore
from chat import Room

__version__ = "0.1.0"

logger = logs.get_logger()


def initiative(room: str, agent: str, user: str, no_act: bool=False, repeat: int|None=None, wait: int|None = None, idle: int|None = None) -> None:
    """Write a system message to prompt an AI agent to talk to a user."""
    rooms_dir = Path(os.environ["ALLEMANDE_ROOMS"])

    room = re.sub(r'\.bb$', '', room)
    room_bb = f"{room}.bb"
    room_file = rooms_dir / room_bb

    if wait:
        delay = random.randint(0, wait)
        logger.info(f"Waiting for a random time up to {wait} seconds: {delay} seconds.")
        time.sleep(delay)

    room_obj = Room(name=room)
    last_messages = room_obj.last(2)
    logger.debug(f"Last messages in {room_bb}: {last_messages}")
    mtime = room_file.stat().st_mtime
    elapsed = time.time() - mtime

    if idle:
        # check that the agent and user have not been chatting recently
        if elapsed < idle and len(last_messages) == 2 and last_messages[0].startswith(f"{user}:\t") and last_messages[1].startswith(f"{agent}:\t"):
            logger.info(f"Agent and user have been chatting recently in {room_bb}. Not sending another message.")
            return

    if repeat is None or elapsed < repeat:
        # Check if the last two messages were an initiative message and a response from the agent
        if len(last_messages) == 2 and last_messages[0].startswith(f"System:\t{agent}, ") and last_messages[1].startswith(f"{agent}:\t"):
            logger.info(f"The last messages in {room_bb} were an initiative message and a response from {agent}. Not sending another message.")
            return

    timestamp = datetime.now().strftime("%A %-I:%M %p")

    logger.info(f"Writing initiative message to {room_bb}, prompting {agent} to talk to {user}.")

    message = f"System:\t{agent}, it's {timestamp}. Please talk to {user}."

    if no_act:
        logger.info(f"Would have written: {message}")
        return

    with room_file.open("a", encoding="utf-8") as f:
        f.write(message + "\n\n")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-n", "--no-act", help="don't actually write the message", action="store_true")
    arg("-r", "--repeat", help="allow repeated messages after this many seconds")
    arg("-w", "--wait", help="wait for a random time up to this many seconds")
    arg("-i", "--idle", help="check that the agent and user have not been chatting recently (seconds)")
    arg("room", help="chat room file name")
    arg("agent", help="name of AI agent to prompt")
    arg("user", help="user to talk to")


if __name__ == "__main__":
    main.go(initiative, setup_args)
