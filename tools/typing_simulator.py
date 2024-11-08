#!/usr/bin/env python3-allemande

"""
typing-simulator.py: Simulate typing by reading from stdin and using xdotool to type each character.
"""

import sys
import time
import random
import subprocess
from typing import TextIO

from argh import arg
from ally import main

__version__ = "0.1.2"

logger = main.get_logger()


def clamp(n: float, minn: float, maxn: float) -> float:
    """Clamp a value between a minimum and maximum."""
    return max(min(maxn, n), minn)


@arg("--mean-delay", help="Mean delay between keystrokes", type=float)
@arg("--sd-delay", help="Standard deviation of delay between keystrokes", type=float)
@arg("--min-delay", help="Minimum delay between keystrokes", type=float)
@arg("--max-delay", help="Maximum delay between keystrokes", type=float)
@arg("--mean-line-delay", help="Mean delay between lines", type=float)
@arg("--sd-line-delay", help="Standard deviation of delay between lines", type=float)
@arg("--min-line-delay", help="Minimum delay between lines", type=float)
@arg("--max-line-delay", help="Maximum delay between lines", type=float)
def typer(
    *filenames: str,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    mean_delay: float = 0.2,
    sd_delay: float = 0.4,
    min_delay: float = 0.05,
    max_delay: float = 1.5,
    mean_line_delay: float = 10,
    sd_line_delay: float = 50,
    min_line_delay: float = 5,
    max_line_delay: float = 30
) -> None:
    """Simulate typing by reading from stdin and using xdotool to type each character."""
    get, put = main.io(istream, ostream)

    logger.info("Starting typing simulation")

    def type_char(char: str) -> None:
        if char == '\n':
            subprocess.run(['xdotool', 'key', '--clearmodifiers', 'Return'], check=True)
        elif char == ' ':
            subprocess.run(['xdotool', 'key', '--clearmodifiers', 'space'], check=True)
        else:
            subprocess.run(['xdotool', 'type', char], check=True)

    def process_input(input_stream: TextIO) -> None:
        while True:
            char = input_stream.read(1)
            if not char:
                break

            delay = clamp(random.normalvariate(mean_delay, sd_delay), min_delay, max_delay)
            time.sleep(delay)

            type_char(char)

            if char == '\n':
                line_delay = clamp(random.normalvariate(mean_line_delay, sd_line_delay), min_line_delay, max_line_delay)
                time.sleep(line_delay)

    if not filenames:
        process_input(istream)
    else:
        for filename in filenames:
            try:
                with open(filename, 'r') as file:
                    process_input(file)
            except IOError as e:
                logger.error(f"Error reading file {filename}: {e}")

    logger.info("Typing simulation completed")


if __name__ == '__main__':
    main.run(typer)

"""
TODO: Implement file processing functionality
FIXME: Consider error handling for xdotool subprocess calls
XXX: Explore ways to make the typing simulation more realistic (e.g., occasional typos, variable typing speed)
"""
