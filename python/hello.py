#!/usr/bin/env python3

import sys
import logging

import argh

__version__ = "1.0.0"

logger = logging.getLogger(__name__)

"""
hello.py - An example Unix-style Python module / script to say hello and copy
or reverse the input.

This script can be used as a module:
    from hello import hello

Example:
    >>> from hello import hello
    >>> hello(["Line 1", "Line 2"], name="Alice", reverse=True)
    ['Line 2', 'Line 1', 'Hello, Alice']
"""

def hello(lines, name="World", reverse=False):
    """
    Processes each line in the given list of lines.

    Args:
        lines (list of str): List of input lines to be processed.
        name (str): Name to be greeted. Defaults to "World".
        reverse (bool): Whether to reverse the lines or not. Defaults to False.

    Returns:
        list of str: List of processed lines.

    Example:
        >>> hello(["How are you?", "Nice day!"], name="Bob", reverse=True)
        ['Nice day!', 'How are you?', 'Hello, Bob']
    """
    lines.insert(0, f"Hello, {name}\n")
    if reverse:
        lines.reverse()
    return lines


@argh.arg('--name', help='name to be greeted')
@argh.arg('--reverse', help='whether to reverse the lines or not')
@argh.arg('--debug', help='enable debug logging')
@argh.arg('--verbose', help='enable verbose logging')
def main(name="World", reverse=False, debug=False, verbose=False):
    """
    hello.py - An example Unix-style Python module / script to say hello and copy
    or reverse the input.

    This script reads lines from stdin and writes the output to stdout.

    Usage:
        cat input.txt | python3 hello.py [--name NAME] [--reverse] [--debug] [--verbose]
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    input_lines = sys.stdin.readlines()
    output_lines = hello(input_lines, name=name, reverse=reverse)
    sys.stdout.writelines(output_lines)

if __name__ == '__main__':
    try:
        argh.dispatch_command(main)
    except Exception as e:
        logger.error(f"Error: %s %s", type(e).__name__, str(e))
        sys.exit(1)
