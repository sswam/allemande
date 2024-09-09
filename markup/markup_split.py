#!/usr/bin/env python3

import sys
import re
import logging

import argh

logger = logging.getLogger(__name__)

"""
markup_split.py - A script to process HTML-like text and split it into lines.

This script can be used as a module:
    from markup_split import process_text
"""

def process_text(text, use_brackets=False):
    """
    Processes the input text by splitting it into lines at tag boundaries.

    Args:
        text (str): Input text to be processed.
        use_brackets (bool): Whether to use square brackets instead of angle brackets.

    Returns:
        str: Processed text with tags split into separate lines.
    """
    open_bracket = '[' if use_brackets else '<'
    close_bracket = ']' if use_brackets else '>'

    open_bracket_esc = re.escape(open_bracket)
    close_bracket_esc = re.escape(close_bracket)

    # Split the text into tags and content
    parts = re.split(f'({open_bracket_esc}[^{close_bracket_esc}]*{close_bracket_esc})', text)

    parts = [p.strip() for p in parts]
    parts = [p for p in parts if p]

    bad = [p for p in parts if re.search(f'.{open_bracket_esc}', p) or re.search(f'{close_bracket_esc}.', p)]
    if bad:
        bad_parts = '\n\n'.join(bad)
        logger.error(f"bad parts:\n\n{bad_parts}")
        sys.exit(1)

    result = '\n'.join(parts) + '\n'

    return result

@argh.arg('--brackets', help='use square brackets instead of angle brackets')
@argh.arg('--debug', help='enable debug logging')
@argh.arg('--verbose', help='enable verbose logging')
def main(brackets=False, debug=False, verbose=False):
    """
    markup_split.py - A script to process HTML-like text and split it into lines.

    This script reads text from stdin and writes the processed output to stdout.

    Usage:
        cat input.txt | python3 markup_split.py [--brackets] [--debug] [--verbose]
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    input_text = sys.stdin.read()
    output_text = process_text(input_text, use_brackets=brackets)
    sys.stdout.write(output_text)

if __name__ == '__main__':
    try:
        argh.dispatch_command(main)
    except Exception as e:
        logger.error(f"Error: %s %s", type(e).__name__, str(e))
        sys.exit(1)
