#!/usr/bin/env python3

import sys
import logging
import requests
import argh

logger = logging.getLogger(__name__)

"""
fetch_images.py - A Python module/script to fetch image URLs from the Civitai images API.

This script can be used as a module:
    from fetch_images import fetch_images
"""

# API Endpoint
API_URL = "https://civitai.com/api/v1/images"

def fetch_images(limit=100, postId=None, modelId=None, modelVersionId=None, username=None, nsfw=None, sort=None, period=None, page=None):
    """
    Fetches image URLs from the Civitai images API.

    Args:
        limit (int): The number of results to be returned per page. Default is 100.
        postId (int): The ID of a post to get images from.
        modelId (int): The ID of a model to get images from.
        modelVersionId (int): The ID of a model version to get images from.
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
        "postId": postId,
        "modelId": modelId,
        "modelVersionId": modelVersionId,
        "username": username,
        "nsfw": nsfw,
        "sort": sort,
        "period": period,
        "page": page
    }

    # Make the request
    response = requests.get(API_URL, params=params)

    if response.status_code != 200:
        raise Exception(f"Failed to fetch images: {response.status_code} {response.text}")

    data = response.json()
    image_urls = [item['url'] for item in data.get('items', [])]

    return image_urls


@argh.arg('--limit', help='number of results to be returned per page, defaults to 100')
@argh.arg('--postId', help='ID of a post to get images from')
@argh.arg('--modelId', help='ID of a model to get images from')
@argh.arg('--modelVersionId', help='ID of a model version to get images from')
@argh.arg('--username', help='filter to images from a specific user')
@argh.arg('--nsfw', help='filter to images that contain mature content')
@argh.arg('--sort', help='order to sort the results')
@argh.arg('--period', help='time frame in which to sort the images')
@argh.arg('--page', help='page to start fetching from')
def main(limit=100, postId=None, modelId=None, modelVersionId=None, username=None, nsfw=None, sort=None, period=None, page=None):
    """
    fetch_images.py - A Python module/script to fetch image URLs from the Civitai images API.

    Usage:
        python3 fetch_images.py [--limit LIMIT] [--postId POSTID] [--modelId MODELID] [--modelVersionId MODELVERSIONID] [--username USERNAME] [--nsfw NSFW] [--sort SORT] [--period PERIOD] [--page PAGE]
    """
    image_urls = fetch_images(limit, postId, modelId, modelVersionId, username, nsfw, sort, period, page)

    for url in image_urls:
        print(url)


if __name__ == '__main__':
    argh.dispatch_command(main)
    try:
        pass
    except Exception as e:
        logger.error(e)
        sys.exit(1)
