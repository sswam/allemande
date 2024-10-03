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

__version__ = "0.1.14"

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

  # Get a copy of the contents of body
  contents = body.contents[:]
  new_contents = []
  index = 0
  stack = []

  while index < len(contents):
    element = contents[index]

    if isinstance(element, Tag) and re.match(r'^h[1-6]$', element.name):
      level = int(element.name[1])

      # Close sections of higher or same level
      while stack and stack[-1]['level'] >= level:
        stack.pop()

      # Create new section
      new_section = soup.new_tag('section', attrs={'class': f'h{level}'})

      # Move heading into new_section
      new_section.append(element)

      # Append new_section
      if stack:
        stack[-1]['section'].append(new_section)
      else:
        new_contents.append(new_section)

      # Push to stack
      stack.append({'level': level, 'section': new_section})

    else:
      # Append to current section or to new_contents
      if stack:
        stack[-1]['section'].append(element)
      else:
        new_contents.append(element)

    index += 1

  # After processing, update body.contents
  body.contents = new_contents

  # Write the processed HTML to the output stream
  put(str(soup))

if __name__ == "__main__":
  main.run(html_sections)
