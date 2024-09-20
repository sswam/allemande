"""
This module provides utilities for terminal interaction and command history management.
"""

import os
import sys
import readline
from pathlib import Path

history_file = None
sys_input = input  # Store the original input function


def is_terminal(stream):
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


def custom_input(*args, **kwargs):
    """
    Custom input function that saves input to history.

    This function wraps the system's input function and saves each input
    to the history file.

    Returns:
        str: The user's input.
    """
    text = sys_input(*args, **kwargs)
    if history_file:
        readline.append_history_file(1, history_file)
    return text


# Replace the built-in input function with our custom one
input = custom_input
