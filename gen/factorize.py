#!/usr/bin/env python3

# Here's a Python program that prompts for a number and factorizes it, written in a style similar to hello.py:

import sys
import logging
import readline
from pathlib import Path
import argh

__version__ = "1.0.0"

history_file = None

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

    readline.set_history_length(-1)
    readline.set_auto_history(True)

def readline_input(*args, **kwargs):
    text = input(*args, **kwargs)
    readline.append_history_file(1, history_file)
    return text

def factorize(n):
    factors = []
    d = 2
    while n > 1:
        while n % d == 0:
            factors.append(d)
            n //= d
        d += 1
        if d * d > n:
            if n > 1:
                factors.append(n)
            break
    return factors

def factorize_number(istream=sys.stdin, ostream=sys.stdout):
    setup_history()

    while True:
        try:
            number_str = readline_input("Enter a positive integer to factorize (or 'q' to quit): ")
            if number_str.lower() == 'q':
                break

            number = int(number_str)
            if number <= 0:
                print("Please enter a positive integer.", file=ostream)
                continue

            factors = factorize(number)
            print(f"The factors of {number} are: {factors}", file=ostream)
        except ValueError:
            print("Invalid input. Please enter a positive integer.", file=ostream)
        except KeyboardInterrupt:
            print("\nExiting...", file=ostream)
            break

@argh.arg('--debug', help='enable debug logging', action='store_const', const=logging.DEBUG, dest='log_level')
@argh.arg('--verbose', help='enable verbose logging', action='store_const', const=logging.INFO, dest='log_level')
@argh.arg('--log-level', help='set log level', default=logging.WARNING)
def main(log_level=logging.WARNING):
    """
    A program to factorize positive integers.

    This script reads from stdin and writes to stdout.

    Usage:
        python factorize.py [--debug] [--verbose]
    """

    global logger

    if log_level == logging.DEBUG:
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    else:
        fmt = "%(message)s"

    logging.basicConfig(level=log_level, format=fmt)
    logger = logging.getLogger(__name__)

    print(log_level, logging.DEBUG)

    try:
        return factorize_number()
    except BaseException as e:
        logger.error("Error: %s %s", type(e).__name__, str(e))
        if log_level == logging.DEBUG:
            raise
        sys.exit(1)

if __name__ == '__main__':
    argh.dispatch_command(main)

# This program:
#
# 1. Prompts the user to enter a positive integer.
# 2. Factorizes the number using a simple trial division algorithm.
# 3. Prints the factors of the number.
# 4. Continues to prompt for numbers until the user enters 'q' to quit.
#
# It includes similar features to hello.py:
# - Command-line argument parsing with argh
# - Logging setup
# - Input history management
# - Error handling
#
# To use this script, save it as `factorize.py` and run it with `python factorize.py`. You can also use the `--debug` or `--verbose` flags for different logging levels.

