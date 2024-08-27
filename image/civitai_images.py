#!/usr/bin/env python3

import sys
import logging
import requests
import argh

logger = logging.getLogger(__name__)

"""
civitai_images.py - A Python module/script to fetch image URLs from the Civitai images API.

This script can be used as a module:
    from civitai_images import fetch_images
"""

# API Endpoint
API_URL = "https://civitai.com/api/v1/images"


def fetch_images(limit=100, post_id=None, model_id=None, model_version_id=None, username=None, nsfw=None, sort=None, period=None, page=1):
    """
    Fetches image URLs from the Civitai images API.

    Args:
        limit (int): The number of results to be returned per request (0-200, default 100).
        post_id (int): The ID of a post to get images from.
        model_id (int): The ID of a model to get images from.
        model_version_id (int): The ID of a model version to get images from.
        username (str): Filter to images from a specific user.
        nsfw (str): Filter to images that contain mature content flags or not.
        sort (str): The order to sort the results.
        period (str): The time frame in which to sort the images.
        page (int): The page to start fetching from.

    Returns:
        list: List of image URLs.
    """

    # Define the query parameters
    params = {
        "limit": limit,
        "postId": post_id,
        "modelId": model_id,
        "modelVersionId": model_version_id,
        "username": username,
        "nsfw": nsfw,
        "sort": sort,
        "period": period,
        "page": page
    }

    # Remove None values from params
    params = {k: v for k, v in params.items() if v is not None}

    # Make the request
    response = requests.get(API_URL, params=params)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch images: {response.status_code} {response.text}")

    data = response.json()
    image_urls = [item['url'] for item in data.get('items', [])]

    return image_urls


@argh.arg('--limit', help='total number of results to be fetched (default 100)', type=int)
@argh.arg('--post-id', help='ID of a post to get images from', type=int)
@argh.arg('--model-id', help='ID of a model to get images from', type=int)
@argh.arg('--model-version-id', help='ID of a model version to get images from', type=int)
@argh.arg('--username', help='filter to images from a specific user')
@argh.arg('--nsfw', help='filter to images that contain mature content (None|Soft|Mature|X)')
@argh.arg('--sort', help='order to sort the results (Most Reactions|Most Comments|Comments|Newest)')
@argh.arg('--period', help='time frame in which to sort the images (|AllTime|Year|Month|Week|Day)')
@argh.arg('--page', help='page to start fetching from', type=int)
@argh.arg('--page-length', help='page length (1 to 200)', type=int)
def main(
    limit = 100,
    post_id = None,
    model_id = None,
    model_version_id = None,
    username = None,
    nsfw = None,
    sort = None,
    period = None,
    page = 1,
    page_length = 100
):
    """
    civitai_images.py - A Python module/script to fetch image URLs from the Civitai images API.

    Usage:
        civitai_images.py [OPTIONS]
    """
    current_page = page if page else 1

    while limit > 0:
        current_page_length = min(page_length, limit)
        image_urls = fetch_images(
            limit=current_page_length,
            post_id=post_id,
            model_id=model_id,
            model_version_id=model_version_id,
            username=username,
            nsfw=nsfw,
            sort=sort,
            period=period,
            page=current_page
        )
        if not image_urls:
            break
        for url in image_urls:
            print(url)
        limit -= len(image_urls)
        current_page += 1


if __name__ == '__main__':
    try:
        argh.dispatch_command(main)
    except Exception as e:
        logger.error(e)
        sys.exit(1)
