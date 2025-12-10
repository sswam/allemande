#!/usr/bin/env python3-allemande

"""
Fetch model information from the Civitai models API.
"""

import os
import json
import requests
from ally import main, logs, yaml, meta  # type: ignore

__version__ = "0.2.0"

logger = logs.get_logger()
API_URL = "https://civitai.com/api/v1/models"
yaml_handler = yaml.create()


def fetch_page(
    url: str,
    limit: int,
    api_key: str | None,
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
) -> tuple[list[dict], str | None]:
    """Fetch a single page of model information from the Civitai models API."""
    params = {
        "limit": limit, "query": query, "tag": tag, "username": username,
        "types": ",".join(types) if types else None, "sort": sort, "period": period,
        "rating": rating, "favorites": favorites, "hidden": hidden,
        "primaryFileOnly": primary_file_only, "nsfw": nsfw,
    }
    request_params = {k: v for k, v in params.items() if v is not None} if url == API_URL else None
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    logger.debug("Request URL: %s", url)
    if request_params:
        logger.debug("Params: %s", json.dumps(request_params))

    try:
        response = requests.get(url, params=request_params, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to fetch models: {e}") from e

    data = response.json()
    models = data.get("items", [])
    next_page_url = data.get("metadata", {}).get("nextPage")
    return models, next_page_url


def get_all_models(**kwargs) -> list[dict]:
    """Fetch and return all models from Civitai based on criteria."""
    all_models = []
    limit = kwargs.pop("limit", 100)
    page_length = kwargs.get("page_length", 100)
    remaining = limit
    current_url: str | None = API_URL
    api_key = kwargs.get("api_key")

    while remaining > 0 and current_url:
        current_length = min(page_length, remaining)
        fetch_args = kwargs.copy()
        models, next_url = meta.call_gently(fetch_page, current_url, limit, **fetch_args)
        if not models:
            break

        all_models.extend(models)
        remaining -= len(models)
        current_url = next_url
    return all_models[:limit]


def print_tsv(models: list[dict]) -> None:
    """Prints a list of models in TSV format."""
    for model in models:
        model_name = model.get("name", "")
        download_count = model.get("stats", {}).get("downloadCount", 0)
        for version in model.get("modelVersions", []):
            version_name = version.get("name", "")
            version_base = version.get("baseModel", "")
            version_words = ", ".join(version.get("trainedWords", []))
            for file in version.get("files", []):
                file_name = file.get("name", "")
                download_url = file.get("downloadUrl", "")
                print(f"{model_name}\t{version_name}\t{file_name}\t{download_url}\t{version_base}\t{version_words}\t{download_count}")


def civitai_models_cli(
    limit: int = 100, page_length: int = 100,
    format_type: str = "tsv", api_key: str | None = None, **kwargs,
) -> None:
    """CLI entry point to fetch and print model information."""
    key = api_key or os.environ.get("CIVITAI_API_KEY")
    all_models = get_all_models(
        limit=limit, page_length=page_length, api_key=key, **kwargs
    )

    if format_type == "tsv":
        print_tsv(all_models)
    elif format_type == "yaml":
        print(yaml_handler.dump(all_models))


def setup_args(arg):
    """Set up command-line arguments."""
    arg("-l", "--limit", help="total number of results to fetch", type=int, default=100)
    arg("-q", "--query", help="search query to filter models by name")
    arg("-t", "--tag", help="search query to filter models by tag")
    arg("-u", "--username", help="filter to specific user's models")
    arg("-T", "--types", help="model types to filter", nargs="+")
    arg("-s", "--sort", help="sort order (Highest Rated|Most Downloaded|Newest)")
    arg("-P", "--period", help="time frame (AllTime|Year|Month|Week|Day)")
    arg("-r", "--rating", help="minimum rating to filter by", type=int)
    arg("-f", "--favorites", help="filter to favorites", action="store_true")
    arg("-H", "--hidden", help="filter to hidden models", action="store_true")
    arg("-p", "--primary-file-only", help="only primary files", action="store_true")
    arg("-n", "--nsfw", help="include NSFW content", action="store_true")
    arg("-c", "--page-length", help="results per page (1-100)", type=int, default=100)
    arg("-F", "--format-type", help="Output format", choices=["tsv", "yaml"], default="tsv")
    arg("-k", "--api-key", help="Civitai API Key (or use CIVITAI_API_KEY env var)")


if __name__ == "__main__":
    main.go(civitai_models_cli, setup_args)
