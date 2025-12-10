#!/usr/bin/env python3-allemande

""" Allemande media library - embeds and ... such! """

import asyncio
import html
import logging
import os
import re
import sys
from urllib.parse import urlparse
import random
from typing import Any
from math import gcd
from collections import deque
from functools import wraps

import markdown
import markdown_it
from markdown_it import MarkdownIt
from mdformat.renderer import MDRenderer
import mdformat_light_touch  # type: ignore
import lxml.html
from mdx_linkify.mdx_linkify import LinkifyExtension
import yt_dlp

import fetch
from ally_room import check_access, safe_path_for_local_file
from bb_lib import lines_to_messages
from ally.quote import quote_words  # type: ignore  # pylint: disable=wrong-import-order
import stamps
from ally.util import asyncify


def get_video_title(url):
    """Get YouTube video title using yt-dlp."""
    ydl_opts = {'quiet': True, 'no_warnings': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return info['title']


async def embed_youtube_links(text):
    """ Replace YouTube links with embeds """
    youtube_pattern = r'(?<!")https://(?:www\.|music\.)?' \
                    r'(?:youtube\.com/watch\?v=|youtu\.be/)' \
                    r'([a-zA-Z0-9_-]{11})' \
                    r'(?:[?&]([^"\s<]*))?'

    async def replace_with_embed(match):
        video_id = match.group(1)
        params = match.group(2)

        # Reconstruct the full URL to fetch title
        full_url = f'https://www.youtube.com/watch?v={video_id}'

        # Fetch title asynchronously
        try:
            get_title_async = asyncify(get_video_title)
            title = await get_title_async(full_url)
            # Escape HTML entities in title
            title = title.replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        except Exception as e:
            print(f"Error fetching title for {video_id}: {e}")
            title = "YouTube video player"

        return (
            f'<iframe width="560" height="315" src="https://www.youtube.com/embed/{video_id}'
            f'{("?" + params) if params else ""}" title="{title}" '
            f'frameborder="0" allow="accelerometer; clipboard-write; encrypted-media; gyroscope; '
            f'picture-in-picture; web-share" referrerpolicy="strict-origin-when-cross-origin" '
            f'allowfullscreen></iframe>'
        )

    # Find all matches first
    matches = list(re.finditer(youtube_pattern, text))

    # Replace each match with its embed (processing async)
    result = text
    offset = 0
    for match in matches:
        embed = await replace_with_embed(match)
        start = match.start() + offset
        end = match.end() + offset
        result = result[:start] + embed + result[end:]
        offset += len(embed) - (end - start)

    return result
