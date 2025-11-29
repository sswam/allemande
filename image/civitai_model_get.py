#!/usr/bin/env python3-allemande

"""
Fetch metadata for a specific model from the Civitai API by URL.
"""

import re
import sys
import json
import requests
from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()
API_TEMPLATE = "https://civitai.com/api/v1/models/{}"


def die(message: str, exit_code: int = 1) -> None:
    """Print an error message to stderr and exit."""
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(exit_code)


def get_model_id_from_url(url: str) -> str:
    """Extracts the model ID from a civitai.com URL."""
    match = re.search(r"/models/(\d+)", url)
    if not match:
        die(f"Could not parse model ID from URL: {url}")
    return match.group(1)


def fetch_model_details(model_id: str) -> dict:
    """Fetches model details from the Civitai API by model ID."""
    api_url = API_TEMPLATE.format(model_id)
    logger.info("Fetching from URL: %s", api_url)
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RuntimeError(f"API request failed: {e}") from e


def civitai_model_get(url: str, metadata: bool = False) -> None:
    """
    Main function to fetch and display model information from a URL.
    """
    model_id = get_model_id_from_url(url)
    data = fetch_model_details(model_id)

    if metadata:
        print(json.dumps(data, indent=2))
        return

    print(f"Name: {data.get('name')} ({data.get('type')})")
    print(f"Creator: {data.get('creator', {}).get('username')}")
    print(f"URL: https://civitai.com/models/{data.get('id')}\n")

    for version in data.get("modelVersions", []):
        print(f"  Version: {version.get('name')}")
        triggers = ", ".join(version.get("trainedWords", []))
        if triggers:
            print(f"    Triggers: {triggers}")

        for file in version.get("files", []):
            print(f"    File: {file.get('name')}")
            print(f"    Size: {file.get('sizeKB'):.2f} KB")
            print(f"    Format: {file.get('metadata', {}).get('format')}")
            print(f"    URL: {file.get('downloadUrl')}\n")


def setup_args(arg):
    """Set up command-line arguments."""
    arg("url", help="The full Civitai model URL")
    arg("-M", "--metadata", help="Display full raw JSON metadata", action="store_true")


if __name__ == "__main__":
    main.go(civitai_model_get, setup_args)
