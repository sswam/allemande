#!/usr/bin/env python3

"""
Fetch image URLs from the Civitai images API.
"""

import sys
import logging
import json

import requests
from ally import main  # type: ignore

__version__ = "0.1.1"

logger = logging.getLogger(__name__)

API_URL = "https://civitai.com/api/v1/images"


def fetch_images(
    limit: int,
    post_id: int | None = None,
    model_id: int | None = None,
    model_version_id: int | None = None,
    username: str | None = None,
    nsfw: str | None = None,
    sort: str | None = None,
    period: str | None = None,
    cursor: str | None = None,
) -> tuple[list[dict], list[str], bool]:
    """Fetch image URLs from the Civitai images API."""
    params = {
        "limit": limit,
        "postId": post_id,
        "modelId": model_id,
        "modelVersionId": model_version_id,
        "username": username,
        "nsfw": nsfw,
        "sort": sort,
        "period": period,
        "cursor": cursor,
    }
    params = {k: v for k, v in params.items() if v is not None}

    try:
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch images: {e}") from e

    data = response.json()
    logger.debug("Data: %s", json.dumps(data))
    items = data.get("items", [])
    urls = [item["url"] for item in items]
    cursor = data["metadata"].get("nextCursor")

    return items, urls, cursor


def civitai_images(
    limit: int = 100,
    post_id: int | None = None,
    model_id: int | None = None,
    model_version_id: int | None = None,
    username: str | None = None,
    nsfw: str | None = None,
    sort: str | None = None,
    period: str | None = None,
    page_length: int = 100,
    metadata: bool = False,
) -> None:
    """Fetch and print image URLs from Civitai."""
    remaining = limit

    cursor = None

    while remaining > 0:
        current_length = min(page_length, remaining)
        items, urls, cursor = fetch_images(
            limit=current_length,
            post_id=post_id,
            model_id=model_id,
            model_version_id=model_version_id,
            username=username,
            nsfw=nsfw,
            sort=sort,
            period=period,
            cursor=cursor,
        )
        if not urls:
            break

        if metadata:
            for item in items:
                print(json.dumps(item))
        else:
            for url in urls:
                print(url)

        remaining -= len(urls)

        if not cursor:
            break


def setup_args(arg):
    """Set up command-line arguments."""
    arg("-l", "--limit", help="total number of results to fetch", type=int)
    arg("-p", "--post-id", help="ID of post to get images from", type=int)
    arg("-m", "--model-id", help="ID of model to get images from", type=int)
    arg("-V", "--model-version-id", help="ID of model version", type=int)
    arg("-u", "--username", help="filter to specific user's images")
    arg("-n", "--nsfw", help="filter mature content (None|Soft|Mature|X)")
    arg("-s", "--sort", help="sort order (Most Reactions|Most Comments|Newest)")
    arg("-P", "--period", help="time frame (AllTime|Year|Month|Week|Day)")
    arg("-c", "--page-length", help="results per page (1-200)", type=int)
    arg("-M", "--metadata", help="display metadata", action="store_true")


if __name__ == "__main__":
    main.go(civitai_images, setup_args)
