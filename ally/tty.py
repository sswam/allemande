"""
This module provides utilities for terminal interaction and command history management.
"""

import os
import sys
import readline
from pathlib import Path
import termios
import tty
import select
from typing import Tuple, Optional


history_file = None


def is_tty(stream):
    """
    Check if the given stream is connected to a terminal.

    Args:
        stream: The stream to check.

    Returns:
        bool: True if connected to a terminal, False if not, None if unknown.
    """
    try:
        return os.isatty(stream.fileno())
    except OSError:
        return None


def setup_history(history_file_path=None):
    """
    Set up command history management.

    Args:
        history_file_path (str, optional): Path to the history file.
            If None, a default path will be used.
    """
    global history_file
    if history_file:
        return

    if not history_file_path:
        history_file_path = Path.home() / f".{Path(sys.argv[0]).stem}_history"

    history_file = str(history_file_path)

    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        # Create the history file if it doesn't exist
        Path(history_file).touch()

    # Unlimited history length
    readline.set_history_length(-1)

    # Enable automatic addition of input to the readline history.
    readline.set_auto_history(True)


def get(*args, placeholder="", **kwargs):
    """
    Custom input function that saves input to history.

    This function wraps the system's input function and saves each input
    to the history file.

    Returns:
        str: The user's input.
    """
    if placeholder:
        readline.set_startup_hook(lambda: readline.insert_text(placeholder))
    try:
        text = input(*args, **kwargs)
    except EOFError:
        text = None
    finally:
        if placeholder:
            readline.set_startup_hook()
    if text is not None:
        readline.append_history_file(1, history_file)
    return text


TTY_CURSOR_POS_TIMEOUT_MS = 100


def _read_with_timeout(fd: int, count: int, timeout_ms: int) -> Optional[bytes]:
    """Read from a file descriptor with a timeout."""
    ready, _, _ = select.select([fd], [], [], timeout_ms / 1000)
    if ready:
        return os.read(fd, count)
    return None


def get_pos() -> Tuple[int, int]:
    """Get the current cursor position in the terminal."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)

    try:
        tty.setraw(fd)

        # Send the cursor position request
        sys.stdout.write("\033[6n")
        sys.stdout.flush()

        # Read the response
        buf = b""
        while True:
            char = read_with_timeout(fd, 1, TIMEOUT_MS)
            if char is None:
                raise TimeoutError("Timeout while reading terminal response")
            buf += char
            if char == b'R':
                break

        # Parse the response
        response = buf.decode()
        if not response.startswith("\033[") or not response.endswith("R"):
            raise ValueError(f"Invalid response: {response}")

        row, col = map(int, response[2:-1].split(';'))
        return row, col

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
