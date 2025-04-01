"""URL fetcher with caching and size limits."""

import hashlib
import os
import time
from pathlib import Path
from urllib.parse import urlparse, quote
import logging

import aiohttp

PATH_WEBCACHE = Path(os.environ["ALLEMANDE_WEBCACHE"])
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
CHUNK_SIZE = 8192
TIMEOUT = aiohttp.ClientTimeout(total=30)
CACHE_TTL = None
HASH_QUERY = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_cached(url: str) -> str:
    """Fetch a URL and cache it, returning the path to the cached file.

    Args:
        url: The URL to fetch and cache

    Returns:
        str: Path to the cached file

    Raises:
        ValueError: If URL is invalid or file is too large
        Exception: If fetching or caching fails
    """

    # 1. Parse and validate URL
    try:
        parsed_url = urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL")
    except Exception as e:
        raise ValueError(f"Invalid URL {url}: {str(e)}") from e

    # 2. Create cache structure
    scheme = parsed_url.scheme
    hostname = quote(parsed_url.netloc)
    path_components = [quote(p) for p in parsed_url.path.split('/') if p]

    filename = path_components[-1] if path_components else 'index'
    if parsed_url.query:
        if HASH_QUERY:
            query_hash = hashlib.sha256(parsed_url.query.encode()).hexdigest()[:8]
            filename = f"{filename}??{query_hash}"
        else:
            # Quote query string to make it filesystem-safe
            filename = f"{filename}?{quote(parsed_url.query)}"

    # 3. Create cache path
    cache_path = Path(PATH_WEBCACHE) / scheme / hostname / '/'.join(path_components[:-1])

    # Sanity check cache_path is under PATH_WEBCACHE
    if not cache_path.resolve().is_relative_to(PATH_WEBCACHE):
        raise ValueError("Invalid URL path")

    cache_path.mkdir(parents=True, exist_ok=True)
    cached_file = cache_path / filename

    # Sanity check cached_file is under cache_path
    if not cached_file.resolve().is_relative_to(cache_path):
        raise ValueError("Invalid URL filename")

    # 4. Return cached version if exists and not expired
    if cached_file.exists():
        # Check file age and remove if too old
        if CACHE_TTL is not None and time.time() - cached_file.stat().st_mtime > CACHE_TTL:
            cached_file.unlink()
        else:
            return str(cached_file)

    # 5. Fetch with aiohttp if not cached
    async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
        try:
            async with session.get(url) as response:
                response.raise_for_status()

#                 # Check content type (optional)
#                 content_type = response.headers.get('content-type', '')
#                 if not content_type.startswith(('image/', 'application/')):
#                     raise ValueError(f"Unsupported content type: {content_type}")

                await save_file(cached_file, response)

        except Exception as e:  # pylint: disable=broad-except
            # Clean up partial downloads
            if cached_file.exists():
                cached_file.unlink()
            logger.error(f"Failed to fetch or cache URL {url}: {str(e)}")
            raise

    return str(cached_file)


async def save_file(cached_file: Path, response: aiohttp.ClientResponse) -> None:
    """Save response content to a file with size limit."""
    total_size = 0
    with open(cached_file, 'wb') as f:
        async for chunk in response.content.iter_chunked(CHUNK_SIZE):
            total_size += len(chunk)
            if total_size > MAX_FILE_SIZE:
                f.close()
                cached_file.unlink()
                raise ValueError(f"File too large (max {MAX_FILE_SIZE} bytes)")
            f.write(chunk)
