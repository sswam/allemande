#!/usr/bin/env python3-allemande

# Certainly! Here's a Python script that reads messy text from stdin, cleans it up, and outputs the result to stdout. This script is inspired by the structure of hello.py and incorporates some of its features:

import sys
import re
import logging
import argparse


logger = logging.getLogger(__name__)


def clean_text(input_text):
    """
    Clean up the input text according to specified requirements.

    Args:
        input_text (str): The input text to clean.

    Returns:
        str: The cleaned text.
    """
    # Split the text into paragraphs
    paragraphs = input_text.split('\n\n')

    cleaned_paragraphs = []
    for paragraph in paragraphs:
        # Ensure consistent capitalization for character names and add colon
        paragraph = re.sub(r'^(?=[^a-z]*$)(.*?[A-Z].*?[A-Z].*?)$(?=\n.*?\S)', r'\1:', paragraph, flags=re.MULTILINE)


        # Remove extra whitespace within each paragraph
        cleaned = re.sub(r'\s+', ' ', paragraph)

        # Remove spaces before commas and periods
        cleaned = re.sub(r'\s+([,.])', r'\1', cleaned)

        # Remove spaces at the beginning of lines
        cleaned = re.sub(r'^\s+', '', cleaned, flags=re.MULTILINE)

        # Remove spaces around apostrophes, but not around quotes
        cleaned = re.sub(r"(?<!\w)'\s|\s'(?!\w)", "'", cleaned)

        # Trim leading and trailing whitespace
        cleaned = cleaned.strip()

        cleaned_paragraphs.append(cleaned)

    for i, paragraph in enumerate(cleaned_paragraphs):
        # Standardize quotation marks
        paragraph = paragraph.replace('"', '"').replace('"', '"')

        # Remove junk "paragraphs".
        if re.match(r'\d*\.$', paragraph):
            paragraph = None

#        if paragraph and len(paragraph) < 10:
#            print("bad paragraph?", paragraph, file=sys.stderr)

        cleaned_paragraphs[i] = paragraph

    # Join paragraphs with double newlines and remove multiple consecutive blank lines
    result = '\n\n'.join(filter(bool, cleaned_paragraphs))
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result


def process_input(input_stream, output_stream):
    """
    Read input from the input stream, clean it, and write to the output stream.

    Args:
        input_stream: The input stream to read from.
        output_stream: The output stream to write to.
    """
    input_text = input_stream.read()
    cleaned_text = clean_text(input_text)
    output_stream.write(cleaned_text)
    output_stream.write('\n')  # Add a newline at the end


def main():
    parser = argparse.ArgumentParser(description="Clean up messy text input.")
    parser.add_argument('--debug', help='enable debug logging', action='store_const', const=logging.DEBUG, dest='log_level')
    parser.add_argument('--verbose', help='enable verbose logging', action='store_const', const=logging.INFO, dest='log_level')
    args = parser.parse_args()

    log_level = args.log_level if args.log_level else logging.WARNING
    logging.basicConfig(level=log_level, format="%(message)s")

    try:
        process_input(sys.stdin, sys.stdout)
    except Exception as e:
        logger.error(f"Error: {type(e).__name__} - {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
