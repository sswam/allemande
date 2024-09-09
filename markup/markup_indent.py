#!/usr/bin/env python3

import sys
import logging
import re

import argh

logger = logging.getLogger(__name__)

"""
markup_indent.py - A script to indent tags in a file and check for mismatched tags.

This script reads from stdin and writes the indented output to stdout.
The input must have tags split out to separate lines, e.g. with htmlsplit.
"""

def process_line(line, level, tag_stack, use_brackets):
    """
    Processes a single line, indenting and checking for mismatched tags.

    Args:
        line (str): The input line to process.
        level (int): The current indentation level.
        tag_stack (list): Stack to keep track of opened tags.
        use_brackets (bool): Whether to use square brackets instead of angle brackets.

    Returns:
        tuple: (processed_line, new_level, error_message)
    """
    open_bracket = '[' if use_brackets else '<'

    match = re.match(rf'\{open_bracket}(/?)(\w+)', line)
    close_tag = match and bool(match.group(1))
    open_tag = match and not close_tag
    tag_name = match and match.group(2)

    if close_tag and (not tag_stack or tag_stack[-1] != tag_name):
        return line, level, f"Mismatched closing tag: {tag_name}"

    if close_tag:
        tag_stack.pop()
        level -= 1

    processed_line = '\t' * level + line

    if open_tag:
        tag_stack.append(tag_name)
        level += 1

    return processed_line, level, None

def indent_tags(lines, use_brackets):
    """
    Indents tags in the given lines and checks for mismatched tags.

    Args:
        lines (list of str): List of input lines to be processed.
        use_brackets (bool): Whether to use square brackets instead of angle brackets.

    Returns:
        list of str: List of processed lines.
    """
    level = 0
    tag_stack = []
    indented = []

    for line in lines:
        processed_line, level, error = process_line(line, level, tag_stack, use_brackets=use_brackets)
        indented.append(processed_line)
        if error:
            for line in indented:
                print(line, end='')
            logger.error(error)
            sys.exit(1)

    if tag_stack:
        logger.error(f"Unclosed tags: {', '.join(tag_stack)}")

    return indented

@argh.arg('--brackets', help='use square brackets instead of angle brackets')
@argh.arg('--debug', help='enable debug logging')
@argh.arg('--verbose', help='enable verbose logging')
def main(brackets=False, debug=False, verbose=False):
    """
    markup_indent.py - A script to indent tags in a file and check for mismatched tags.

    This script reads from stdin and writes the indented output to stdout.

    Usage:
        cat input.txt | python3 markup_indent.py [--brackets] [--debug] [--verbose]
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    input_lines = sys.stdin.readlines()
    output_lines = indent_tags(input_lines, use_brackets=brackets)
    for line in output_lines:
        sys.stdout.write(line)

if __name__ == '__main__':
    try:
        argh.dispatch_command(main)
    except Exception as e:
        logger.error(f"Error: %s %s", type(e).__name__, str(e))
        raise
        sys.exit(1)
