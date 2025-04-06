#!/usr/bin/env python3-allemande

""" Allemande bb file utilities """

import sys
from pathlib import Path
import logging
from typing import Any, TextIO, IO, Iterator, cast
from dataclasses import dataclass

from util import Symbol


USER_NARRATIVE = Symbol("Narrative")
USER_CONTINUED = Symbol("Continued")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ChatMessage:
    """A single chat message with user (optional) and content."""

    user: str | None
    content: str


def split_message_line(line):
    """Split a message line into user and content."""

    if not line.endswith("\n"):
        line += "\n"

    if "\t" in line:
        label, content = line.split("\t", 1)
    else:
        label = None
        content = line

    logger.debug("split_message_line line, label, content: %r, %r, %r", line, label, content)

    if label is None:
        user = USER_NARRATIVE
    elif label == "":
        user = USER_CONTINUED
    elif label.endswith(":"):
        user = label[:-1]
    else:
        logger.warning("Invalid label missing colon, in line: %s", line)
        user = USER_NARRATIVE
        content = label + "\t" + content

    return user, content


def lines_to_messages(lines: Iterator[str | bytes]) -> Iterator[dict[str, Any]]:
    """A generator to convert an iterable of lines to chat messages."""

    message: dict | None = None

    lines = iter(lines)
    skipped_blank = 0

    while True:
        line = next(lines, None)
        if line is None:
            break

        if isinstance(line, bytes):
            line = line.decode("utf-8")

        # skip blank lines
        if line.rstrip("\r\n") == "":
            skipped_blank += 1
            continue

        user, content = split_message_line(line)

        # accumulate continued lines
        if message and user == USER_CONTINUED:  # pylint: disable=unsupported-assignment-operation
            message["content"] += "\n" * skipped_blank + content  # pylint: disable=unsupported-assignment-operation
            skipped_blank = 0
            continue

        if not message and user == USER_CONTINUED:
            logger.warning("Continued line with no previous incomplete message: %s", line)
            user = USER_NARRATIVE

        if message and user == USER_NARRATIVE and "user" not in message:  # pylint: disable=unsupported-membership-test
            message["content"] += "\n" * skipped_blank + content  # pylint: disable=unsupported-assignment-operation
            skipped_blank = 0
            continue

        # yield the previous message
        if message:
            logger.debug(message)
            yield message
            message = None

        # start a new message
        skipped_blank = 0
        if user == USER_NARRATIVE:
            message = {"content": content}
        else:
            message = {"user": user, "content": content}

    if message is not None:
        logger.debug(message)
        yield message


def test_split_message_line():
    """Test split_message_line."""
    line = "Ally:	Hello\n"
    user, content = split_message_line(line)
    assert user == "Ally"
    assert content == "Hello\n"


def test_lines_to_messages():
    """Test lines_to_messages."""
    lines = """Ally:	Hello
World
Sam:	How are you?
"""
    messages = list(lines_to_messages(lines.splitlines()))
    assert len(messages) == 2
    assert messages[0]["user"] == "Ally"
    assert messages[0]["content"] == "Hello\nWorld\n"
    assert messages[1]["user"] == "Sam"
    assert messages[1]["content"] == "How are you?\n"


def message_to_text(message: dict[str, Any]) -> str:
    """Convert a chat message to text."""
    user = message.get("user")
    content = message["content"]
    if user:
        lines = content.splitlines() or [""]
        lines2 = []
        lines2.append(f"{user}:\t{lines[0]}\n")
        for line in lines[1:]:
            lines2.append(f"\t{line}\n")
        text = "".join(lines2)
    else:
        text = content
    return text.rstrip("\n") + "\n"


def messages_to_lines(messages):
    """Convert chat messages to lines."""
    for message in messages:
        yield message_to_text(message)


def chat_message_to_text(message: ChatMessage) -> str:
    """Convert a chat message to text."""
    return message_to_text({"user": message.user, "content": message.content})


def load_chat_messages(source: str | Path | TextIO = sys.stdin) -> list[ChatMessage]:
    """Parse chat messages from a file path or file-like object.

    Args:
        source: Path to input file, Path object, or file-like object (defaults to stdin)

    Returns:
        List of ChatMessage records
    """
    # Handle file-like objects directly
    if hasattr(source, "read"):
        return [ChatMessage(content=msg["content"], user=msg.get("user")) for msg in lines_to_messages(cast(Iterator[str], source))]

    # Handle path inputs
    path = Path(source) if isinstance(source, str) else source
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        return load_chat_messages(f)


def save_chat_messages(messages: list[ChatMessage], destination: str | Path | TextIO | IO[Any] = sys.stdout, mode: str = "a") -> None:
    """Write chat messages to a file path or file-like object.

    Args:
        messages: List of ChatMessage objects to write
        destination: Output file path, Path object, or file-like object (defaults to stdout)
        mode: File open mode when writing to a path, defaults to 'a' for append
    """
    # Handle file-like objects directly
    if hasattr(destination, "write"):
        for msg in messages:
            destination.write(chat_message_to_text(msg) + "\n")
        return

    # Handle path outputs
    path = Path(destination) if isinstance(destination, str) else destination
    with path.open(mode, encoding="utf-8") as f:
        save_chat_messages(messages, f)
