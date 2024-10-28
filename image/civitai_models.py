#!/usr/bin/env python3

"""
Download LoRAs and other models from CivitAI, optionally getting all versions.

Environment:
  CIVITAI_API_KEY: API key for CivitAI (required)
"""

import sys
import os
import logging
import requests
from pathlib import Path
import re

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logging.getLogger(__name__)

API_URL = "https://civitai.com/api/v1/models"
API_KEY = os.environ.get("CIVITAI_API_KEY")


def download_model(url: str, filename: str | None = None) -> None:
    """Download a model file from the given URL."""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    response = requests.get(url, stream=True, headers=headers)
    response.raise_for_status()

    if not filename:
        filename = response.headers.get('content-disposition', '').split('filename=')[-1]
        if not filename:
            filename = url.split('/')[-1]

    # Strip quotes if present
    filename = re.sub(r'^"|"$', r'', filename)

    path = Path(filename)

    # Check if file already exists
    if path.exists():
        logger.warning("File already exists, skipping download: %s", path.name)
        return

    total = int(response.headers.get('content-length', 0))
    logger.info(f"Downloading {path.name} ({total / 1024 / 1024:.1f} MB)")

    with open(path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def fetch_model(model_id: int, version_id: int | None = None, all_versions: bool = False) -> None:
    """Fetch a specific model version or latest version."""
    url = f"{API_URL}/{model_id}"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    if not data.get('modelVersions'):
        raise Exception(f"No versions found for model {model_id}")

    versions = data['modelVersions']

    logger.info(f"Model: %d: %s", model_id, data['name'])

    if version_id:
        versions = [v for v in versions if v['id'] == version_id]
        if not versions:
            raise Exception(f"Version {version_id} not found")
    elif not all_versions:
        versions = [versions[-1]]

    logger.info(f"Versions: %s", ', '.join(str(v['id']) for v in versions))

    for version in versions:
        for file in version['files']:
            download_model(file['downloadUrl'])


def parse_civitai_url(url: str) -> tuple[int, int | None]:
    """Extract model ID and version ID from a CivitAI URL.

    Args:
        url: CivitAI URL like https://civitai.com/models/352581?modelVersionId=988765

    Returns:
        Tuple of (model_id, version_id) where version_id may be None
    """
    import re
    from urllib.parse import urlparse, parse_qs

    # Handle full URLs
    if url.startswith(('http://', 'https://')):
        parsed = urlparse(url)
        path_match = re.match(r'/models/(\d+)', parsed.path)
        if not path_match:
            raise ValueError(f"Invalid CivitAI URL format: {url}")
        model_id = int(path_match.group(1))

        # Check for version in query params
        query_params = parse_qs(parsed.query)
        version_id = query_params.get('modelVersionId', [None])[0]
        return model_id, int(version_id) if version_id else None

    # Handle plain numbers
    if url.isdigit():
        return int(url), None

    raise ValueError(f"Input must be a CivitAI URL or numeric ID: {url}")

def download_models(
    *model_ids: str | int,
    all_versions: bool = False,
    version: int | None = None
) -> None:
    """Download one or more models from CivitAI.

    Args:
        model_ids: List of model IDs (as numbers or URLs)
        all_versions: Whether to download all versions of each model
        version: Specific version to download (ignored if all_versions is True)
    """
    if version and all_versions:
        raise ValueError("Cannot specify both --version and --all-versions")

    fail = 0
    for model_input in model_ids:
        try:
            # Parse the input to get model_id and possible version override
            model_id, url_version = parse_civitai_url(str(model_input))

            # Use URL version unless overridden by all_versions or explicit version
            version_to_use = version if version else url_version
            if all_versions:
                version_to_use = None

            fetch_model(model_id, version_to_use, all_versions)
        except Exception as e:
            logger.error(f"Failed to download model {model_input}: {e}")
            fail = 1

    return fail


def setup_args(arg):
    """Set up command-line arguments."""
    arg("model_ids", nargs='*', help="CivitAI model IDs or URLs to download")
    arg("-a", "--all-versions", action="store_true", help="download all versions")
    arg("-v", "--version", help="download specific version")


if __name__ == "__main__":
    main.go(download_models, setup_args)
