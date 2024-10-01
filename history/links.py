#!/usr/bin/env python3

"""
This module extracts links from the an HTML or Markdown input,
optionally filtering them based on the provided base URL.
"""

import sys
import logging
from typing import TextIO
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import markdown
from argh import arg

from ally import main
from ally.lazy import lazy

__version__ = "0.1.0"

logger = main.get_logger()


lazy('requests')


def is_internal_link(base_url: str, link: str) -> bool:
    """Check if the given link is internal to the base URL."""
    parsed_base = urlparse(base_url)
    parsed_link = urlparse(link)
    return parsed_base.netloc == parsed_link.netloc


def extract_links_from_html(html_content: str, base_url: str) -> list[str]:
    """Extract links from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
#    toc = soup.find('nav', class_='toc')  # Adjust this selector based on the HTML structure
    toc = soup.find('nav')
    if not toc:
        logger.warning("Table of contents not found in HTML.")
        return []
    return [urljoin(base_url, a['href']) for a in toc.find_all('a', href=True)]


def extract_links_from_markdown(md_content: str, base_url: str) -> list[str]:
    """Extract links from Markdown content."""
    html = markdown.markdown(md_content)
    return extract_links_from_html(html, base_url)


def filter_links(links: list[str], base_url: str, external: bool) -> list[str]:
    """Filter links based on whether they are internal or external."""
    if external:
        return [link for link in links if not is_internal_link(base_url, link)]
    return [link for link in links if is_internal_link(base_url, link)]


@arg("base_url", help="Base URL for filtering internal links")
@arg("--external", help="Output only external links", action="store_true")
@arg("--all", help="Output all links without filtering", action="store_true")
def links(
    base_url: str,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    external: bool = False,
    all: bool = False,
) -> None:
    """
    Extract links from the table of contents of an HTML or Markdown input,
    and output them based on the specified options.
    """
    get, put = main.io(istream, ostream)

    content = get(all=True)

    if content.strip().startswith('<!DOCTYPE html>') or content.strip().startswith('<html'):
        links = extract_links_from_html(content, base_url)
    else:
        links = extract_links_from_markdown(content, base_url)

    if all:
        filtered_links = links
    else:
        filtered_links = filter_links(links, base_url, external)

    for link in filtered_links:
        put(link)

    if not filtered_links:
        logger.warning("No links found matching the specified criteria.")


if __name__ == "__main__":
    main.run(links)
