#!/usr/bin/env python3

import sys
import re
import logging

import argh

logger = logging.getLogger(__name__)

"""
filter_email.py - A script to filter out links and other unwanted elements from email text.

This script can be used as a module:
    from filter_email import filter_email
"""

def filter_email(lines, remove_links=True, remove_images=True):
    """
    Processes each line in the given list of lines to remove unwanted elements.

    Args:
        lines (list of str): List of input lines to be processed.
        remove_links (bool): Whether to remove links or not.
        remove_images (bool): Whether to remove image references or not.

    Returns:
        list of str: List of processed lines.
    """
    filtered_lines = []
    for line in lines:
        if remove_links:
            # Remove markdown-style links
            line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', line)
            
            # Remove reference-style links (e.g., [OpenAI Developer Forum][1])
            line = re.sub(r'\[([^\]]+)\]\[\d+\]', r'\1', line)
            
            # Remove URLs and surrounding guff
            line = re.sub(r'(\[ *|\( *|\[\d+\]: *)?http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+( *\]| *\))?', '', line)

        if remove_images:
            # Remove image references
            line = re.sub(r'View image: \(.*?\)', '', line)

        # Remove empty lines
        if line.strip():
            filtered_lines.append(line)

    return filtered_lines

@argh.arg('--keep-links', help='keep links in the text')
@argh.arg('--keep-images', help='keep image references in the text')
@argh.arg('--debug', help='enable debug logging')
@argh.arg('--verbose', help='enable verbose logging')
def main(keep_links=False, keep_images=False, debug=False, verbose=False):
    """
    filter_email.py - A script to filter out links and other unwanted elements from email text.

    This script reads lines from stdin and writes the filtered output to stdout.

    Usage:
        cat email.txt | python3 filter_email.py [--keep-links] [--keep-images] [--debug] [--verbose]
    """
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
    elif verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        logging.getLogger().setLevel(logging.WARNING)

    input_lines = sys.stdin.readlines()
    output_lines = filter_email(input_lines, remove_links=not keep_links, remove_images=not keep_images)
    for line in output_lines:
        sys.stdout.write(line)

if __name__ == '__main__':
    try:
        argh.dispatch_command(main)
    except Exception as e:
        logger.error(e)
        sys.exit(1)
