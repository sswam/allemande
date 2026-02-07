#!/usr/bin/env python3-allemande

"""
Invoke an Ally Chat agent from the command line via temporary room files.
"""

import sys
import shutil
import asyncio
import os
import time
from pathlib import Path
from typing import TextIO

import aionotify  # type: ignore

from ally import main, logs  # type: ignore
from bb_lib import lines_to_messages, message_to_text, ChatMessage

__version__ = "0.1.3"

logger = logs.get_logger()

DEFAULT_ROOMS_DIR = Path(os.getenv("ALLEMANDE_ROOMS", "rooms"))
TEMP_ROOM_BASE = "ally_chat_cli"
DEBOUNCE_DELAY = 0.5  # seconds to wait after last file change
DEFAULT_TIMEOUT = 120.0  # seconds to wait for response


def cleanup_temp_dir(temp_dir: Path) -> None:
    """Clean up temporary directory, logging any errors."""
    try:
        shutil.rmtree(temp_dir)
    except Exception:  # pylint: disable=broad-except
        logger.warning("Failed to clean up temp directory: %s", temp_dir)


def create_room_content(
    user: str,
    query: str,
    contexts: list[str] | None = None,
) -> str:
    """Create the .bb format content for the room file."""
    content = ""

    # Add context files with headers if provided
    if contexts:
        for context in contexts:
            if context == "-":
                stdin_content = sys.stdin.read()
                content += f"#File: stdin\n\n{stdin_content}\n\n"
            else:
                context_path = Path(context)
                if context_path.is_file():
                    with open(context_path) as f:
                        file_content = f.read()
                    content += f"#File: {context_path.name}\n\n{file_content}\n\n"

    # Add the user's query message
    if query:
        if user:
            # Normal case: user message with name
            msg = ChatMessage(user=user, content=query)
            content += message_to_text({"user": msg.user, "content": msg.content}) + "\n"
        else:
            # Special case: raw query without user attribution
            content += query.rstrip() + "\n\n"

    return content


async def create_temp_room(rooms_dir: Path) -> Path:
    """Create a uniquely named temporary room directory."""
    base_path = rooms_dir / TEMP_ROOM_BASE
    base_path.mkdir(parents=True, exist_ok=True)

    # Try creating directory with timestamp
    max_attempts = 100
    for _ in range(max_attempts):
        timestamp = time.time()
        nano = time.time_ns()
        dir_name = f"{timestamp:.0f}.{nano % 1000000000:09d}"
        temp_dir = base_path / dir_name

        try:
            temp_dir.mkdir(exist_ok=False)
            return temp_dir
        except FileExistsError:
            # Collision detected, yield and retry
            await asyncio.sleep(0)
            continue

    raise RuntimeError(f"Failed to create temp directory after {max_attempts} attempts")


def parse_bb_messages(content: str) -> list[tuple[str | None, str]]:
    """Parse .bb format content into list of (name, message) tuples."""
    messages = []
    for msg_dict in lines_to_messages(content.splitlines(keepends=True)):
        user = msg_dict.get("user")
        content_text = msg_dict["content"].rstrip("\n")
        messages.append((user, content_text))
    return messages


async def wait_for_response(
    room_file: Path,
    initial_message_count: int,
    num_messages: int = 1,
    timeout: float = DEFAULT_TIMEOUT,
) -> list[tuple[str | None, str]]:
    """Wait for agent response(s) using inotify, with debouncing."""
    watcher = aionotify.Watcher()
    watch_dir = room_file.parent
    watcher.watch(
        str(watch_dir),
        aionotify.Flags.MODIFY | aionotify.Flags.MOVED_TO,
    )
    await watcher.setup(asyncio.get_event_loop())

    start_time = time.time()
    last_event_time: float | None = None
    expected_message_count = initial_message_count + num_messages

    try:
        while True:
            elapsed = time.time() - start_time

            # Check timeout
            if elapsed > timeout:
                raise TimeoutError(f"No response received within {timeout} seconds")

            # Wait for event with remaining timeout
            remaining_timeout = timeout - elapsed
            try:
                event = await asyncio.wait_for(
                    watcher.get_event(),
                    timeout=min(remaining_timeout, 1.0),
                )
            except asyncio.TimeoutError:
                # Check if we have a pending debounce
                if last_event_time and (time.time() - last_event_time) >= DEBOUNCE_DELAY:
                    # Check if we have enough messages
                    content = room_file.read_text()
                    messages = parse_bb_messages(content)
                    if len(messages) >= expected_message_count:
                        break
                continue

            if event and event.name == room_file.name:
                last_event_time = time.time()

            # Check if debounce period has elapsed
            if last_event_time and (time.time() - last_event_time) >= DEBOUNCE_DELAY:
                # Check if we have enough messages
                content = room_file.read_text()
                messages = parse_bb_messages(content)
                if len(messages) >= expected_message_count:
                    break

        # Read the file and extract new messages
        content = room_file.read_text()
        messages = parse_bb_messages(content)

        # Return only new messages
        if len(messages) > initial_message_count:
            return messages[initial_message_count:]

        raise RuntimeError("File changed but no new messages found")

    finally:
        watcher.close()


async def ally_chat_cli_async(
    user: str,
    agent: str | None,
    query: str,
    contexts: list[str] | None = None,
#     missions: list[str] | None = None,
#     options: dict | None = None,
    num_messages: int = 1,
    keep: bool = False,
    directory: Path | None = None,
    timeout: float = DEFAULT_TIMEOUT,
    rooms_dir: Path = DEFAULT_ROOMS_DIR,
) -> tuple[list[tuple[str | None, str]], Path | None]:
    """
    Invoke an Ally Chat agent asynchronously.

    Returns:
        tuple of (list of (name, content) tuples, temp_dir_path or None)
    """
    # If agent is given, prepend @ mention
    if agent:
        query = f"@{agent}, "
    # If directory specified, use it and imply keep
    if directory:
        temp_dir = directory
        room_file = temp_dir / "chat.bb"
        keep = True

        # Count existing messages
        if room_file.exists():
            existing_content = room_file.read_text()
            initial_message_count = len(parse_bb_messages(existing_content))
        else:
            initial_message_count = 0

        # Append new content
        room_content = create_room_content(user, query, contexts)
        with open(room_file, "a") as f:
            f.write(room_content)
    else:
        # Create room content
        room_content = create_room_content(user, query, contexts)
        initial_message_count = len(parse_bb_messages(room_content))

        # Create temp directory
        temp_dir = await create_temp_room(rooms_dir)
        room_file = temp_dir / "chat.bb"

        try:
            # Write content to temp file first
            temp_file = temp_dir / ".chat.bb.tmp"
            temp_file.write_text(room_content)

            # Atomic move into place
            temp_file.rename(room_file)
        except Exception:
            # Clean up on error
            cleanup_temp_dir(temp_dir)
            raise

    # Wait for response
    try:
        response_messages = await wait_for_response(
            room_file, initial_message_count, num_messages, timeout
        )

        if keep:
            return response_messages, temp_dir

        # Clean up temp directory
        cleanup_temp_dir(temp_dir)
        return response_messages, None

    except Exception:
        # Clean up on error unless keeping
        if not keep and not directory:
            cleanup_temp_dir(temp_dir)
        raise


def format_bb_output(messages: list[tuple[str | None, str]]) -> str:
    """Format a list of (name, content) tuples as .bb format."""
    output_parts = []
    for name, content in messages:
        if name:
            msg_dict = {"user": name, "content": content}
        else:
            msg_dict = {"content": content}
        output_parts.append(message_to_text(msg_dict))
    return "".join(output_parts)


def ally_chat_cli(
    ostream: TextIO,
    user: str = "",
    agent: str | None = None,
    query: str = "",
    contexts: list[str] | None = None,
    num_messages: int = 1,
    keep: bool = False,
    directory: str = "",
    timeout: float = DEFAULT_TIMEOUT,
) -> None:
    """CLI wrapper for ally_chat_cli_async."""
    if not user and query:
        # Special case: no user means raw query format
        pass
    elif not user:
        import getpass
        user = getpass.getuser().title()

    dir_path = Path(directory) if directory else None

    response_messages, temp_dir = asyncio.run(
        ally_chat_cli_async(
            user=user,
            agent=agent,
            query=query,
            contexts=contexts,
            num_messages=num_messages,
            keep=keep,
            directory=dir_path,
            timeout=timeout,
        )
    )

    if keep and temp_dir:
        ostream.write(f"{temp_dir.name}\n")

    output = format_bb_output(response_messages)
    ostream.write(output)
    if not output.endswith("\n"):
        ostream.write("\n")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-u", "--user", help="name of user (omit for raw query format)")
    arg("-a", "--agent", help="agent to invoke (omit to use @ mentions in query)")
    arg("query", nargs="?", help="query to send (empty string for none)")
    arg("contexts", nargs="*", help="context files to include")
    arg("-n", "--num-messages", type=int, help="number of response messages expected")
    arg("-k", "--keep", action="store_true", help="keep temporary room directory")
    arg("-d", "--directory", help="use existing room directory (implies --keep)")
    arg("-t", "--timeout", type=float, help=f"timeout in seconds (default: {DEFAULT_TIMEOUT})")


if __name__ == "__main__":
    main.go(ally_chat_cli, setup_args)
