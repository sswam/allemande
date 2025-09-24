#!/usr/bin/env python3-allemande

"""
Extract links and images from markdown files, output as TSV.
"""

from typing import TextIO, Iterator
import urllib.parse
from markdown_it import MarkdownIt
from markdown_it.token import Token

from ally import main, logs  # type: ignore[import-untyped]

__version__ = "0.1.6"

logger = logs.get_logger()


def _extract_link(children: list[Token], index: int) -> tuple[str, str, str, int]:
    """Extracts URL and text from a link token sequence."""
    link_open_token = children[index]
    url = dict(link_open_token.attrs or {}).get('href', '')

    text_parts = []
    i = index + 1
    while i < len(children) and children[i].type != 'link_close':
        token = children[i]
        if token.content:
            text_parts.append(token.content)
        i += 1

    text = "".join(text_parts)
    # Return the new index pointing to the link_close token. The outer loop
    # will increment it past the link.
    return 'link', str(url), text, i


def _extract_image(token: Token) -> tuple[str, str, str]:
    """Extracts URL and alt text from an image token."""
    url = dict(token.attrs or {}).get('src', '')
    alt = token.content or ''
    return 'image', str(url), str(alt)


def _traverse_tokens(tokens: list[Token]) -> Iterator[tuple[str, str, str]]:
    """Recursively traverse tokens to find links and images."""
    for token in tokens:
        if token.type == 'inline' and token.children:
            children = token.children
            i = 0
            while i < len(children):
                child = children[i]
                if child.type == 'link_open':
                    _type, url, text, i = _extract_link(children, i)
                    yield _type, url, text
                elif child.type == 'image':
                    _type, url, text = _extract_image(child)
                    yield _type, url, text
                i += 1
        elif token.children:
            # Only recurse if this isn't an inline token we already processed
            yield from _traverse_tokens(token.children)


def extract_links(text: str) -> Iterator[tuple[str, str, str]]:
    """Extract links and images from markdown text using markdown-it."""
    md = MarkdownIt()
    tokens = md.parse(text)
    yield from _traverse_tokens(tokens)


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
