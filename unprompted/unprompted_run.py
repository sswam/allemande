#!/usr/bin/env python3-allemande

"""
Command-line interface for running Unprompted templates.
Processes input from arguments or stdin and applies Unprompted template language.
"""

import os
import sys
import logging
import random
from pathlib import Path

import argh

unprompted_dir = str((Path(__file__).resolve().parent / "unprompted").resolve())
sys.path.insert(0, unprompted_dir)

# Import after adding unprompted_dir to sys.path
from lib_unprompted.shared import Unprompted  # pylint: disable=import-error,wrong-import-position

logger = logging.getLogger(__name__)


def process_unprompted(input_string, seed=None):
    """
    Process input string through Unprompted template engine.

    Args:
        input_string: The template string to process
        seed: Optional seed value for random operations

    Returns:
        Processed output from Unprompted
    """
    unprompted = Unprompted()

    # Use provided seed or generate a random one
    if seed is None:
        seed = random.randint(0, 2**32-1)

    unprompted.shortcode_user_vars = {"seed": seed}
    result = unprompted.start(input_string)
    unprompted.cleanup()
    unprompted.goodbye()
    return result


@argh.arg("--debug", help="enable debug logging")
@argh.arg("--verbose", help="enable verbose logging")
@argh.arg("--seed", help="seed for random operations (integer)", type=int)
def main(*inp, debug=False, verbose=False, seed=None):
    """
    Process input text with Unprompted template engine.

    Input can be provided as command line arguments or through stdin.
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    cwd = os.getcwd()
    os.chdir(unprompted_dir)

    try:
        if inp:
            input_string = " ".join(inp)
        else:
            input_string = sys.stdin.read()

        output = process_unprompted(input_string, seed)
        print(output)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error: %s %s", type(e).__name__, str(e))
        sys.exit(1)
    finally:
        os.chdir(cwd)


if __name__ == "__main__":
    argh.dispatch_command(main)
