#!/usr/bin/env python3

"""
This module adds <section> tags around headings and their content in HTML files.

Usage:
    python3 html_sections.py < input.html > output.html

The script reads HTML from stdin and writes the processed HTML to stdout.
"""

import sys
import logging
from typing import TextIO
import re

from argh import arg
from bs4 import BeautifulSoup, Tag

from ally import main

__version__ = "0.1.8"

logger = main.get_logger()

def html_sections(
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Add <section> tags around headings and their content in HTML files.

    Args:
        istream (TextIO): Input stream to read HTML content from.
        ostream (TextIO): Output stream to write processed HTML content to.
    """
    # Set up input and output streams
    get, put = main.io(istream, ostream)

    # Read all content from input stream
    content = get(all=True)

    # Parse HTML content
    soup = BeautifulSoup(content, 'html.parser')
    body = soup.body if soup.body else soup

    # Find all heading tags (h1 to h6)
    headings = body.find_all(re.compile(r'^h[1-6]$'))
    stack = []

    # Process each heading
    for heading in headings:
        level = int(heading.name[1])

        # Remove sections from stack if they're at the same or higher level
        while stack and stack[-1]['level'] >= level:
            stack.pop()

        # Create a new section tag and wrap the heading
        section = soup.new_tag('section', attrs={'class': f'h{level}'})
        heading.wrap(section)

        # Add the new section to the stack
        stack.append({'level': level, 'section': section})

    # Process content after each heading
    for section_info in stack:
        section = section_info['section']
        next_element = section.next_sibling
        while next_element and not (isinstance(next_element, Tag) and re.match(r'^h[1-6]$', next_element.name)):
            following_element = next_element.next_sibling
            section.append(next_element)
            next_element = following_element

    # Write the processed HTML to the output stream
    put(str(soup))

if __name__ == "__main__":
    main.run(html_sections)
