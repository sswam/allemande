#!/usr/bin/env python3-allemande

import sys
import logging
import re

import argh

import markup_split

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

"""
markup_indent.py - A script to indent tags in a file and check for mismatched tags.

This script reads from stdin and writes the indented output to stdout.
The input must have tags split out to separate lines, e.g. with htmlsplit.
"""

DEFAULT_HTML_SINGLETON_TAGS = {
    'area', 'base', 'basefont', 'bgsound', 'br', 'col', 'command', 'embed',
    'hr', 'img', 'input', 'isindex', 'keygen', 'link', 'meta', 'param',
    'plaintext', 'source', 'track', 'wbr',
    '!doctype', '!--'
}

def process_line(line, level, tag_stack, use_brackets, singleton_tags):
    """
    Processes a single line, indenting and checking for mismatched tags.

    Args:
        line (str): The input line to process.
        level (int): The current indentation level.
        tag_stack (list): Stack to keep track of opened tags.
        use_brackets (bool): Whether to use square brackets instead of angle brackets.
        singleton_tags (set): Set of singleton tag names.

    Returns:
        tuple: (processed_line, new_level, error_message)
    """
    open_bracket = '[' if use_brackets else '<'
    close_bracket = ']' if use_brackets else '>'

    open_bracket_esc = re.escape(open_bracket)
    close_bracket_esc = re.escape(close_bracket)

    match = re.match(rf'{open_bracket_esc}(/?)([^\s{close_bracket_esc}]+)', line)

    tag_name = match and match.group(2).lower()
    close_tag = match and bool(match.group(1))
    singleton_tag = match and not close_tag and tag_name in singleton_tags
    open_tag = match and not (close_tag or singleton_tag)
    tag_type = 'close' if close_tag else 'singleton' if singleton_tag else 'open' if open_tag else None

    logger.debug("tag %s %s", tag_name, tag_type)

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

def indent_tags(lines, use_brackets, singleton_tags):
    """
    Indents tags in the given lines and checks for mismatched tags.

    Args:
        lines (list of str): List of input lines to be processed.
        use_brackets (bool): Whether to use square brackets instead of angle brackets.
        singleton_tags (set): Set of singleton tag names.

    Returns:
        list of str: List of processed lines.
    """
    level = 0
    tag_stack = []
    indented = []

    for line in lines:
        processed_line, level, error = process_line(line, level, tag_stack, use_brackets, singleton_tags)
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
@argh.arg('-s', '--single', help='comma-separated list of singleton tags')
@argh.arg('-H', '--not_html', help='do not use default HTML singleton tags, implied by -b', action='store_true')
def main(brackets=False, debug=False, verbose=False, single=None, not_html=False):
    """
    markup_indent.py - A script to indent tags in a file and check for mismatched tags.

    This script reads from stdin and writes the indented output to stdout.

    Usage:
        cat input.txt | python3 markup_indent.py [--brackets] [--debug] [--verbose] [-s SINGLE_TAGS] [--not_html]
    """
    if debug:
        logger.setLevel(logging.DEBUG)
    elif verbose:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    if not_html:
        singleton_tags = set()
    else:
        singleton_tags = DEFAULT_HTML_SINGLETON_TAGS
    if single:
        singleton_tags = singleton_tags.union({t.lower() for t in single.split(',')})

    input_text = sys.stdin.read()
    split_text = markup_split.process_text(input_text, use_brackets=brackets)
    input_lines = split_text.splitlines(keepends=True)

    output_lines = indent_tags(input_lines, use_brackets=brackets, singleton_tags=singleton_tags)
    for line in output_lines:
        sys.stdout.write(line)

if __name__ == '__main__':
    try:
        argh.dispatch_command(main)
    except Exception as e:
        logger.error(f"Error: %s %s", type(e).__name__, str(e))
        # raise
        sys.exit(1)
