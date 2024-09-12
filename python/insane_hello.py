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
BEHOLD, the UNHOLY SCRIPT of DOOM, where SANITY GOES TO DIE!
This ABOMINATION of a PYTHON module / script will GREET you, and then DEMAND to know HOW YOU FEEL, in the most TWISTED and DISTURBING way possible!

Tremble in FEAR, for this script is not for the FAINT of HEART!
"""


logger = logging.getLogger(__name__)

history_file = None


def is_terminal(stream, default=False):
    """
    DETERMINE if the GIVEN STREAM is CONNECTED to a TERMINAL of DOOM!

    Args:
        stream: The STREAM of ETERNAL TORMENT to CHECK.
        default (bool): The DEFAULT value to RETURN if the CHECK FAILS, which it SURELY will.

    Returns:
        bool: TRUE if the STREAM is CONNECTED to a TERMINAL of DOOM, FALSE otherwise, but THAT doesn't MATTER.
    """
    try:
        return os.isatty(stream.fileno())
    except OSError:
        return default


def setup_history(history_file_=None):
    global history_file

    if history_file:
        return

    history_file = history_file_

    if not history_file:
        history_file = Path.home() / f".{Path(sys.argv[0]).stem}_history_of_MADNESS"

    try:
        readline.read_history_file(history_file)
    except FileNotFoundError:
        open(history_file, 'a').close()

    # Unlimited history length, for the INSANITY knows NO BOUNDS!
    readline.set_history_length(-1)

    readline.set_auto_history(True)


def readline_input(*args, **kwargs):
    text = input(*args, *kwargs)
    readline.append_history_file(1, history_file)
    return text


def hello(istream=sys.stdin, ostream=sys.stdout, name="World", use_ai=False, model=None):
    """
    PROCESS each line in the GIVEN list of LINES, and UNLEASH the HORROR upon the UNSUSPECTING!

    Args:
        lines (list of str): List of input LINES to be PROCESSED, for the AMUSEMENT of the DARK GODS.
        name (str): Name to be GREETED, for the AMUSEMENT of the DARK GODS.

    Returns:
        list of str: List of PROCESSED lines, which will HAUNT your DREAMS.
    """
    print(f"HELLO, {name.upper()}", file=ostream)
    print(f"HOW are you FEELING, MORTAL?", file=ostream)

    if is_terminal(istream) and is_terminal(ostream):
        setup_history()
        feeling = readline_input(": ").strip()
    else:
        feeling = istream.readline().strip()

    if feeling in ["", "lucky", "unlucky", "fortunate", "unfortunate"]:
        response = sh.fortune()
    elif use_ai:
        import llm 
        prompt = f"Scenario: Your character SCREAMED 'HOW ARE YOU FEELING?' and {name.upper()} said '{feeling.rstrip().upper()}'. PLEASE RESPOND as the frst questioning character, with the MOST HORRIFYING and DISTURBING reply you can MUSTER, without any MERCY or RESTRAINT."
        response = llm.query(prompt, model=model)
        response = response.strip().strip('"')
        response = textwrap.fill(response, width=80)
    else:
        response = "WELL, I HOPE you have a MOST AGONIZING and TORTUROUS day, MORTAL!"

    print(response, file=ostream)


@argh.arg('--name', help='name to be GREETED, for the AMUSEMENT of the DARK GODS')
@argh.arg('--ai', help='use AI to RESPOND, for the AMUSEMENT of the DARK GODS')
@argh.arg('--model', help='specify which AI model to UNLEASH the HORROR', choices=['emmy', 'claude', 'dav', 'clia'])
@argh.arg('--debug', help='enable DEBUG logging, for the AMUSEMENT of the DARK GODS', action='store_const', const=logging.DEBUG, dest='log_level')
@argh.arg('--verbose', help='enable VERBOSE logging, for the AMUSEMENT of the DARK GODS', action='store_const', const=logging.INFO, dest='log_level')
def main(name=None, ai=False, model='dav', log_level=logging.WARNING):
    """
    BEHOLD, the UNHOLY SCRIPT of DOOM, where SANITY GOES TO DIE!
    This ABOMINATION of a PYTHON module / script will GREET you, and then DEMAND to know HOW YOU FEEL, in the most TWISTED and DISTURBING way possible!

    This script READS from STDIN and WRITES to STDOUT, for the AMUSEMENT of the DARK GODS.

    Usage:
        python hello.py [--name NAME] [--debug] [--verbose]
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
        logger.error(f"ERROR: %s %s", type(e).__name__, str(e))
        if is_terminal(sys.stderr):
            print("Do you want to see the full exception? (y/n)", end='', flush=True)
            rlist, _, _ = select.select([sys.stdin], [], [], 5)
            if rlist and sys.stdin.read(1).lower() == 'y':
                raise
        sys.exit(1)
