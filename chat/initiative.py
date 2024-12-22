#!/usr/bin/env python3-allemande

"""
Send a System message to a chat room, to prompt an AI to message a user at a certain time

Example use, from crontab:

0 * * * * /home/sam/allemande/chat/initiative.py -i 1800 -r 28800 -w 600 sam Ally Sam

This will prompt the AI agent Ally to talk with the user Sam in the chat room
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

__version__ = "0.1.1"

logger = logs.get_logger()


def should_prompt_for_initiative(
    last_messages: list[str],
    agent: str,
    user: str,
    elapsed: float,
    idle: int | None,
    repeat: int | None
) -> bool:
    """Check if we should skip sending an initiative message."""
    if len(last_messages) != 2:
        logger.info("Not enough messages to skip sending an initiative message.")
        return True

    # Check if the agent and user have been chatting recently
    recent_chat = (
        idle is not None
        and elapsed < idle
        and last_messages[0].startswith(f"{user}:\t")
        and last_messages[1].startswith(f"{agent}:\t")
    )
    if recent_chat:
        logger.info("Agent and user have been chatting recently. Not sending another message.")
        return False

    # Check if last messages were an initiative and agent response
    was_initiative = (
        (repeat is None or elapsed < repeat)
        and last_messages[0].startswith(f"System:\t{agent}, ")
        and last_messages[1].startswith(f"{agent}:\t")
    )
    if was_initiative:
        logger.info(
            "The last messages were an initiative message and a response from %s. Not sending another message.",
            agent
        )
        return False

    return True


def initiative(
    room: str,
    agent: str,
    user: str,
    no_act: bool = False,
    repeat: int | None = None,
    wait: int | None = None,
    idle: int | None = None,
    message: str = "",
    prompt: bool = True,
    timestamp: bool = True,
) -> None:
    """Write a system message to prompt an AI agent to talk with a user."""
    rooms_dir = Path(os.environ["ALLEMANDE_ROOMS"])
    room = re.sub(r"\.bb$", "", room)
    room_bb = f"{room}.bb"
    room_file = rooms_dir / room_bb

    if wait:
        delay = random.randint(0, wait)
        logger.info("Waiting for a random time up to %d seconds: %d seconds", wait, delay)
        time.sleep(delay)

    room_obj = Room(name=room)
    try:
        last_messages = room_obj.last(2)
    except FileNotFoundError:
        logger.debug("Room file not found: %s", room_bb)
        last_messages = []
    logger.debug("Last messages in %s: %s", room_bb, last_messages)
    try:
        mtime = room_file.stat().st_mtime
    except FileNotFoundError:
        mtime = 0
    elapsed = time.time() - mtime

    if not should_prompt_for_initiative(last_messages, agent, user, elapsed, idle, repeat):
        return

    now = datetime.now().strftime("%A %-I:%M %p")
    logger.info("Writing initiative message to %s, prompting %s to talk with %s", room_bb, agent, user)

    system_message = f"System:\t{agent}, "
    if timestamp:
        system_message += f"it's {now}. "
    if prompt:
        system_message += f"Please talk with {user}. "
    system_message += message.format(now=now, user=user)
    system_message = system_message.strip()

    if no_act:
        logger.info("Would have written: %s", system_message)
        return

    with room_file.open("a", encoding="utf-8") as f:
        f.write(system_message + "\n\n")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-n", "--no-act", help="don't actually write the message", action="store_true")
    arg("-r", "--repeat", help="allow repeated messages after this many seconds")
    arg("-w", "--wait", help="wait for a random time up to this many seconds")
    arg("-i", "--idle", help="check that the agent and user have not been chatting recently (seconds)")
    arg("-m", "--message", help="message to write, can use {now} and {user}")
    arg(
        "-T",
        "--no-timestamp",
        help="don't automatically include a timestamp in the message",
        action="store_false",
        dest="timestamp",
    )
    arg(
        "-P",
        "--no-prompt",
        help="don't automatically include a prompt to talk to the user in the message",
        action="store_false",
        dest="prompt",
    )
    arg("room", help="chat room file name")
    arg("agent", help="name of AI agent to prompt")
    arg("user", help="user to talk with")


if __name__ == "__main__":
    main.go(initiative, setup_args)
