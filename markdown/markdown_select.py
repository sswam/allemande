#!/usr/bin/env python3-allemande

"""
Extract links and images from markdown files, output as TSV.
"""

import re
from typing import TextIO, Iterator
import urllib.parse

from ally import main, logs

__version__ = "0.1.1"

logger = logs.get_logger()


def extract_links(text: str) -> Iterator[tuple[str, str, str]]:
    """Extract links and images from markdown text."""

    for match in re.finditer(r'(!?)\[([^]]*)\]\(([^)]+)\)', text):
        is_image = match.group(1) == '!'
        type_ = 'image' if is_image else 'link'
        yield (type_, match.group(3), match.group(2))


def process_markdown(
    istream: TextIO,
    ostream: TextIO,
    images: bool = False,
    links: bool = False,
    base: str | None = None,
) -> None:
    """Process markdown and output TSV of links/images."""
    content = istream.read()

    if images and links:
        logger.warning("Both --images and --links specified; defaulting to all.")
        images = links = False

    # Get all matches
    matches = list(extract_links(content))

    # Filter based on options
    if images:
        matches = [(t, u, x) for t, u, x in matches if t == 'image']
    elif links:
        matches = [(t, u, x) for t, u, x in matches if t == 'link']
    show_type = not (images or links)
    for type_, url, text in matches:
        if base:
            # use url module to join base and url
            url = urllib.parse.urljoin(base, url)
        type2 = type_ + "\t" if show_type else ""
        ostream.write(f"{type2}{url}\t{text}\n")


def setup_args(arg):
    """Set up command-line arguments."""
    arg("-i", "--images", action="store_true", help="output only images")
    arg("-l", "--links", action="store_true", help="output only links")
    arg("-b", "--base", help="base URL for relative links")


if __name__ == "__main__":
    main.go(process_markdown, setup_args)
