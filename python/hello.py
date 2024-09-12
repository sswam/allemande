#!/usr/bin/env python3

import os
import sys
import logging
import getpass
import textwrap
import readline
import select

from pathlib import Path

import argh
import sh


import readline
import atexit


"""
hello.py - An example Python module / script to say hello,
and ask the user how they are.

This script can be used as a module:
    from hello import hello
"""


logger = logging.getLogger(__name__)

history_file = None


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


def readline_input(*args, **kwargs):
    text = input(*args, *kwargs)
    readline.append_history_file(1, history_file)
    return text


def hello(istream=sys.stdin, ostream=sys.stdout, name="World", use_ai=False, model=None):
    """
    Processes each line in the given list of lines.

    Args:
        lines (list of str): List of input lines to be processed.
        name (str): Name to be greeted.

    Returns:
        list of str: List of processed lines.
    """
    print(f"Hello, {name}", file=ostream)
    print(f"How are you feeling?", file=ostream)

    if is_terminal(istream) and is_terminal(ostream):
        setup_history()
        feeling = readline_input(": ").strip()
    else:
        feeling = istream.readline().strip()

    if feeling in ["", "lucky", "unlucky", "fortunate", "unfortunate"]:
        response = sh.fortune()
    elif use_ai:
        import llm 
        prompt = f"Scenario: Your character asked 'How are you feeling?' and {name} said '{feeling.rstrip()}'. Please reply directly without any prelude, disclaimers or explanation."
        response = llm.query(prompt, model=model)
        response = response.strip().strip('"')
        response = textwrap.fill(response, width=80)
    else:
        response = "Well, I hope you have a great day!"

    print(response, file=ostream)


@argh.arg('--name', help='name to be greeted')
@argh.arg('--ai', help='use AI to respond')
@argh.arg('--model', help='specify which AI model', choices=['emmy', 'claude', 'dav', 'clia'])
@argh.arg('--debug', help='enable debug logging', action='store_const', const=logging.DEBUG, dest='log_level')
@argh.arg('--verbose', help='enable verbose logging', action='store_const', const=logging.INFO, dest='log_level')
def main(name=None, ai=False, model='clia', log_level=logging.WARNING):
    """
    An example Unix-style Python module / script to say hello,
    and ask the user how they are.

    This script reads from stdin and writes to stdout.

    Usage:
        python hello.py [--name NAME] [--ai] [--model {emmy,claude,dav,clia}] [--debug] [--verbose]
    """

    if log_level == logging.DEBUG:
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    else:
        fmt = "%(message)s"
    logging.basicConfig(level=log_level, format=fmt)

    if not name:
        name = getpass.getuser().title()

    return hello(name=name, use_ai=ai, model=model)


if __name__ == '__main__':
    try:
        argh.dispatch_command(main)
    except Exception as e:
        logger.error(f"Error: %s %s", type(e).__name__, str(e))
        if is_terminal(sys.stderr):
            print("Do you want to see the full exception? (y/n)", end='', flush=True)
            rlist, _, _ = select.select([sys.stdin], [], [], 5)
            if rlist and sys.stdin.read(1).lower() == 'y':
                raise
        sys.exit(1)
