import os
import sys
import readline
from pathlib import Path


history_file = None

sys_input = input


def is_terminal(stream):
    """
    Check if the given stream is connected to a terminal.

    Args:
        stream: The stream to check.
        default (bool): The default value to return if the check fails.

    Returns:
        bool: True if connected to a terminal, False if not, None if unknown.
    """
    try:
        return os.isatty(stream.fileno())
    except OSError:
        return None


def setup_history(history_file_=None):
    global history_file
    if history_file:
        return

    history_file = history_file_

    if not history_file:
        history_file = Path.home() / f".{Path(sys.argv[0]).stem}_history"

    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        pass

    # Unlimited history length
    readline.set_history_length(-1)

    readline.set_auto_history(True)


def input(*args, **kwargs):
    text = sys_input(*args, *kwargs)
    readline.append_history_file(1, history_file)
    return text
