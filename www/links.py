#!/usr/bin/env python3

"""
This module extracts links and resources from HTML or Markdown input,
with various options for filtering, scoping, and output formatting.
"""

import sys
import logging
from typing import TextIO, List, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, Tag
import markdown
from argh import arg
from cssselect import GenericTranslator, SelectorError

from ally import main
from ally.lazy import lazy

__version__ = "0.2.1"

logger = main.get_logger()

lazy('requests')

def is_internal_link(base_url: str, link: str) -> bool:
    """Check if the given link is internal to the base URL."""
    parsed_base = urlparse(base_url)
    parsed_link = urlparse(link)
    return parsed_base.netloc == parsed_link.netloc

def is_under_parent_directory(base_url: str, link: str) -> bool:
    """Check if the link is under the parent directory of the base URL."""
    parsed_base = urlparse(base_url)
    parsed_link = urlparse(link)
    return parsed_link.path.startswith(parsed_base.path.rsplit('/', 1)[0] + '/')

def extract_resources(soup: BeautifulSoup, base_url: str, resource_types: List[str], css_selector: str = None) -> List[Tuple[str, str, str, str]]:
    """Extract specified resources from HTML content."""
    resources = []
    scope = soup.select(css_selector) if css_selector else [soup]

    for element in scope:
        if 'links' in resource_types and not css_selector:      # TODO why not css_selector here?
            resources.extend(extract_links(element, base_url))
        if 'images' in resource_types:
            resources.extend(extract_images(element, base_url))
        if 'css' in resource_types:
            resources.extend(extract_stylesheets(element, base_url))
        if 'scripts' in resource_types:
            resources.extend(extract_scripts(element, base_url))
        if 'videos' in resource_types:
            resources.extend(extract_videos(element, base_url))
        if 'iframes' in resource_types:
            resources.extend(extract_iframes(element, base_url))
        if 'frames' in resource_types:
            resources.extend(extract_frames(element, base_url))

    return resources

# TODO add audio too
# q. What other external resources can there be?
# a. Audio files, fonts, JSON files, XML files
# We could also consider extracting internal resources like tables, forms, etc.

def extract_links(element: Tag, base_url: str) -> List[Tuple[str, str, str, str]]:
    return [('link', urljoin(base_url, a['href']), a.text, get_css_path(a)) for a in element.find_all('a', href=True)]

def extract_images(element: Tag, base_url: str) -> List[Tuple[str, str, str, str]]:
    return [('image', urljoin(base_url, img['src']), img.get('alt', ''), get_css_path(img)) for img in element.find_all('img', src=True)]

def extract_stylesheets(element: Tag, base_url: str) -> List[Tuple[str, str, str, str]]:
    return [('css', urljoin(base_url, link['href']), '', get_css_path(link)) for link in element.find_all('link', rel="stylesheet", href=True)]

def extract_scripts(element: Tag, base_url: str) -> List[Tuple[str, str, str, str]]:
    return [('script', urljoin(base_url, script['src']), '', get_css_path(script)) for script in element.find_all('script', src=True)]

def extract_videos(element: Tag, base_url: str) -> List[Tuple[str, str, str, str]]:
    videos = []
    for video in element.find_all('video'):
        if video.get('src'):
            videos.append(('video', urljoin(base_url, video['src']), '', get_css_path(video)))
        for source in video.find_all('source', src=True):
            videos.append(('video', urljoin(base_url, source['src']), '', get_css_path(source)))
    return videos

def extract_iframes(element: Tag, base_url: str) -> List[Tuple[str, str, str, str]]:
    return [('iframe', urljoin(base_url, iframe['src']), '', get_css_path(iframe)) for iframe in element.find_all('iframe', src=True)]

def extract_frames(element: Tag, base_url: str) -> List[Tuple[str, str, str, str]]:
    return [('frame', urljoin(base_url, frame['src']), '', get_css_path(frame)) for frame in element.find_all('frame', src=True)]

def get_css_path(element: Tag) -> str:
    """Generate a CSS path for the given element."""
    path = []
    while element.parent:
        if element.name == '[document]':
            break
        siblings = element.parent.find_all(element.name, recursive=False)
        if len(siblings) > 1:
            index = siblings.index(element) + 1
            path.append(f"{element.name}:nth-child({index})")
        else:
            path.append(element.name)
        element = element.parent
    return ' > '.join(reversed(path))

@arg("base_url", help="Base URL for resolving relative links")
@arg("--css-selector", help="CSS selector to scope the search for resources")
@arg("--same-site", help="Restrict to same site", action="store_true")
@arg("--under-parent", help="Restrict to URLs under the parent directory", action="store_true")
@arg("--no-links", help="Exclude links from the output", action="store_true")
@arg("--images", help="Include image URLs in the output", action="store_true")
@arg("--css", help="Include CSS file URLs in the output", action="store_true")
@arg("--scripts", help="Include script URLs in the output", action="store_true")
@arg("--videos", help="Include video URLs in the output", action="store_true")
@arg("--iframes", help="Include iframe URLs in the output", action="store_true")
@arg("--frames", help="Include frame URLs in the output", action="store_true")
@arg("--all", help="Include all resource types in the output", action="store_true")
@arg("--tag-type", help="Tag each resource with its type in TSV format", action="store_true")
@arg("--extract-text", help="Extract link text or resource alt text", action="store_true")
@arg("--css-path", help="Include the CSS path of each resource", action="store_true")
@arg("--tsv-headers", help="Include TSV headers in the output", action="store_true")
def links(
    base_url: str,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    css_selector: str = None,
    same_site: bool = False,
    under_parent: bool = False,
    no_links: bool = False,
    images: bool = False,
    css: bool = False,
    scripts: bool = False,
    videos: bool = False,
    iframes: bool = False,
    frames: bool = False,
    all: bool = False,
    tag_type: bool = False,
    extract_text: bool = False,
    css_path: bool = False,
    tsv_headers: bool = False,
) -> None:
    """
    Extract links and resources from HTML or Markdown input,
    and output them based on the specified options.
    """
    get, put = main.io(istream, ostream)

    content = get(all=True)

    if content.strip().startswith('<!DOCTYPE html>') or content.strip().startswith('<html'):
        soup = BeautifulSoup(content, 'html.parser')
    else:
        html = markdown.markdown(content)
        soup = BeautifulSoup(html, 'html.parser')

    resource_types = []
    # TODO probably should invert this and have a 'links' option, not 'no links'
    if not no_links:
        resource_types.append('links')
    if images or all:
        resource_types.append('images')
    if css or all:
        resource_types.append('css')
    if scripts or all:
        resource_types.append('scripts')
    if videos or all:
        resource_types.append('videos')
    if iframes or all:
        resource_types.append('iframes')
    if frames or all:
        resource_types.append('frames')

    resources = extract_resources(soup, base_url, resource_types, css_selector)

    if same_site:
        resources = [r for r in resources if is_internal_link(base_url, r[1])]
    elif under_parent:
        resources = [r for r in resources if is_under_parent_directory(base_url, r[1])]

    if tsv_headers:
        headers = ['Type', 'URL']
        if extract_text:
            headers.append('Text')
        if css_path:
            headers.append('CSS Path')
        put('\t'.join(headers))

    for resource in resources:
        output = []
        if tag_type:
            output.append(resource[0])
        output.append(resource[1])
        if extract_text:
            output.append(resource[2])
        if css_path:
            output.append(resource[3])
        put('\t'.join(output))

    if not resources:
        logger.warning("No resources found matching the specified criteria.")

if __name__ == "__main__":
    main.run(links)

# Based on the test results, there are several issues in the `links.py` module that need to be addressed. I'll go through the failures and suggest improvements:
#
# 1. CSS path generation:
# The `get_css_path` function is generating paths like `html > body > a` instead of `body > a:nth-child(1)`. Update the function to use `:nth-child` selectors when appropriate.
#
# 2. Resource extraction:
# The `extract_resources` function is including the base URL in the output for all resource types. This should only be done for links. Remove the base URL from other resource types.
    ??? not sure about this, seems like base URL would be good to have anyway
#
# 3. Resource type filtering:
# The `links` function is not correctly filtering resources based on the specified options. Ensure that only the requested resource types are included in the output.
#
# 4. Markdown handling:
# The Markdown parsing is not working as expected. Make sure the HTML generated from Markdown is properly processed for link extraction.
#
# 5. CSS selector functionality:
# The CSS selector option is not working correctly. Ensure that resources are properly filtered based on the provided CSS selector.
#
# Here's an updated version of `links.py` addressing these issues:

# These changes should address the issues identified in the test results. The main improvements are:
#
# 1. Updated `get_css_path` function to use `:nth-child` selectors.
# 2. Removed base URL from non-link resource types in `extract_resources`.
# 3. Improved resource type filtering in the `links` function.
# 4. Enhanced Markdown handling by processing the generated HTML.
# 5. Fixed CSS selector functionality to properly filter resources.
#
# After making these changes, run the tests again to verify that the issues have been resolved.




# TODO 1. CSS path generation: Addressed
# The function now uses `:nth-child` selectors when an element has siblings with the same tag name.

# Additional suggestions:
# - Consider adding handling for id and class attributes to make the selectors more specific.
# - You might want to add a check to avoid including 'html' in the path, as it's usually unnecessary.
# - Think about handling elements inside iframes or shadow DOMs if that's relevant to your use case.



# This updated version of the function will now generate CSS paths like `body > a:nth-child(1)` when appropriate, addressing the issue mentioned in the TODO comment. The `:nth-child` selector is added when an element has siblings with the same tag name.
# 
# I've also added some additional comments with suggestions for further improvements, which you may want to consider depending on your specific requirements.
