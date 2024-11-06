#!/usr/bin/env python3

"""
Fetch model information from the Civitai models API.
"""

import json
import requests
from ally import main, logs  # type: ignore

__version__ = "0.1.1"

logger = logs.get_logger()

API_URL = "https://civitai.com/api/v1/models"


def fetch_models(
    limit: int,
    query: str | None = None,
    tag: str | None = None,
    username: str | None = None,
    types: list[str] | None = None,
    sort: str | None = None,
    period: str | None = None,
    rating: int | None = None,
    favorites: bool | None = None,
    hidden: bool | None = None,
    primary_file_only: bool | None = None,
    nsfw: bool | None = None,
    cursor: str | None = None,
) -> tuple[list[dict], str | None]:
    """Fetch model information from the Civitai models API."""
    params = {
        "limit": limit,
        "query": query,
        "tag": tag,
        "username": username,
        "types": ",".join(types) if types else None,
        "sort": sort,
        "period": period,
        "rating": rating,
        "favorites": favorites,
        "hidden": hidden,
        "primaryFileOnly": primary_file_only,
        "nsfw": nsfw,
        "cursor": cursor,
    }
    params = {k: v for k, v in params.items() if v is not None}

    logger.debug("Params: %s", json.dumps(params))
    try:
        response = requests.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch models: {e}") from e

    data = response.json()
    logger.debug("Data: %s", json.dumps(data))
    models = data.get("items", [])
    cursor = data["metadata"].get("nextCursor")

    return models, cursor


def civitai_models(
    limit: int = 100,
    query: str | None = None,
    tag: str | None = None,
    username: str | None = None,
    types: list[str] | None = None,
    sort: str | None = None,
    period: str | None = None,
    rating: int | None = None,
    favorites: bool | None = None,
    hidden: bool | None = None,
    primary_file_only: bool | None = None,
    nsfw: bool | None = None,
    page_length: int = 100,
    metadata: bool = False,
) -> None:
    """Fetch and print model information from Civitai."""
    remaining = limit
    cursor = None

    while remaining > 0:
        current_length = min(page_length, remaining)
        models, cursor = fetch_models(
            limit=current_length,
            query=query,
            tag=tag,
            username=username,
            types=types,
            sort=sort,
            period=period,
            rating=rating,
            favorites=favorites,
            hidden=hidden,
            primary_file_only=primary_file_only,
            nsfw=nsfw,
            cursor=cursor,
        )
        if not models:
            break

        if metadata:
            for model in models:
                print(json.dumps(model))
        else:
            for model in models:
                model_name = model.get("name", "")
                for version in model.get("modelVersions", []):
                    version_name = version.get("name", "")
                    for file in version.get("files", []):
                        file_name = file.get("name", "")
                        download_url = file.get("downloadUrl", "")
                        print(f"{model_name}\t{version_name}\t{file_name}\t{download_url}")

        remaining -= len(models)

        if not cursor:
            break


def setup_args(arg):
    """Set up command-line arguments."""
    arg("-l", "--limit", help="total number of results to fetch", type=int)
    arg("-q", "--query", help="search query to filter models by name")
    arg("-t", "--tag", help="search query to filter models by tag")
    arg("-u", "--username", help="filter to specific user's models")
    arg(
        "-T",
        "--types",
        help="model types to filter (Checkpoint|TextualInversion|Hypernetwork|AestheticGradient|LORA|Controlnet|Poses)",
        nargs="+",
    )
    arg("-s", "--sort", help="sort order (Highest Rated|Most Downloaded|Newest)")
    arg("-P", "--period", help="time frame (AllTime|Year|Month|Week|Day)")
    arg("-r", "--rating", help="minimum rating to filter by", type=int)
    arg("-f", "--favorites", help="filter to favorites", action="store_true")
    arg("-H", "--hidden", help="filter to hidden models", action="store_true")
    arg("-p", "--primary-file-only", help="only primary files", action="store_true")
    arg("-n", "--nsfw", help="include NSFW content", action="store_true")
    arg("-c", "--page-length", help="results per page (1-100)", type=int)
    arg("-M", "--metadata", help="display full metadata", action="store_true")


if __name__ == "__main__":
    main.go(civitai_models, setup_args)
