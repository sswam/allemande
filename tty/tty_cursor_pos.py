#!/usr/bin/env python3
"""
A script to get the current cursor position in a terminal.

This script demonstrates how to:
1. Set the terminal to raw mode
2. Send the Device Status Report (DSR) escape sequence
3. Read the response, which is in the format "\033[row;colR"
4. Parse the response to extract row and column numbers
5. Restore the original terminal settings

The script can be used as a module:
    from get_terminal_position import get_pos
"""

import sys
import os
import termios
import tty
import select
from typing import Tuple, Optional

from ally import main

__version__ = "1.0.0"

logger = main.get_logger()

TIMEOUT_MS = 100


def read_with_timeout(fd: int, count: int, timeout_ms: int) -> Optional[bytes]:
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

        y, x = map(int, response[2:-1].split(';'))
        return y, x

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def main_get_pos() -> None:
    """Main function to get the cursor position."""
    try:
        y, x = get_pos()
        print(f"row={y} col={x}")
    except Exception as e:
        logger.error(f"Failed to get cursor position: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main.run(main_get_pos)
