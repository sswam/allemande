#!/usr/bin/env python3

import sys
import logging

import argh


logger = logging.getLogger(__name__)


"""
hello.py - An example Unix-style Python module / script to say hello and copy
or reverse the input.

This script can be used as a module:
    from hello import hello
"""


def hello(lines, name="World", reverse=False):
    """
    Processes each line in the given list of lines.

    Args:
        lines (list of str): List of input lines to be processed.
        name (str): Name to be greeted.
        reverse (bool): Whether to reverse the lines or not.

    Returns:
        list of str: List of processed lines.
    """
    lines.insert(0, f"Hello, {name}")
    if reverse:
        lines = lines[::-1]
    return lines


@argh.arg('--name', help='name to be greeted')
@argh.arg('--reverse', help='whether to reverse the lines or not')
def main(name="World", reverse=False):
    """
    hello.py - An example Unix-style Python module / script to say hello and copy
    or reverse the input.

    This script reads lines from stdin and writes the output to stdout.

    Usage:
        cat input.txt | python3 hello.py [--name NAME] [--reverse]
    """
    input_lines = sys.stdin.readlines()
    output_lines = hello(input_lines, name=name, reverse=reverse)
    for line in output_lines:
        sys.stdout.write(line)


if __name__ == '__main__':
    try:
        argh.dispatch_command(main)
    except Exception as e:
        logger.error(e)
        sys.exit(1)
