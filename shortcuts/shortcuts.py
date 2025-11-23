#!/usr/bin/env python3-allemande

""" Service to handle shortcuts for the Allemande platform. """

import logging
import os
from pathlib import Path
from urllib.parse import urljoin

from starlette.applications import Starlette
from starlette.responses import RedirectResponse, PlainTextResponse
from starlette.exceptions import HTTPException

from ally import logs  # type: ignore

logger = logs.get_logger()

SHORTCUTS_DIR = Path(os.environ["ALLEMANDE_HOME"])/"site/s"

app = Starlette()

# Configure basic logging. # Removed as per changes.


def get_content_or_url(shortcut_name: str) -> tuple[str, str] | None:
    """
    Safely reads the content or URL for a shortcut.

    Checks if the path is a regular file or symlink within the shortcuts dir.
    For regular files, returns ('content', file_content).
    For symlinks, returns ('redirect', target_url), handling relative URLs.
    Returns None if not found or invalid.
    """
    file_path = SHORTCUTS_DIR / shortcut_name

    if file_path.is_symlink():
        # Symlink: get URL and handle relative
        link_target = os.readlink(str(file_path))
        site_url = os.environ["ALLEMANDE_SITE_URL"]
        base_path = "/s/" + shortcut_name
        if not base_path.endswith('/'):
            base_path += '/'
        base_url = site_url + base_path
        url = urljoin(base_url, link_target)
        return ('redirect', url)

    # Regular file? return content
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return ('content', content)
    except Exception as e:
        logger.error("Error reading file '%s': %s", file_path, e)

    return None


@app.route("/{shortcut_name:str}")
async def handle_redirect(request):
    """
    Main endpoint to handle a shortcut request.
    """
    shortcut_name = request.path_params["shortcut_name"]
    logger.info("Request for shortcut: %s", shortcut_name)
    result = get_content_or_url(shortcut_name)

    # Fail fast if not found
    if result is None:
        logger.warning("Shortcut not found: %s", shortcut_name)
        raise HTTPException(status_code=404)

    rtype, value = result
    if rtype == 'redirect':
        logger.info("Redirecting '%s' -> '%s'", shortcut_name, value)
        # Issue a temporary (302) redirect.
        return RedirectResponse(value, status_code=302)
    elif rtype == 'content':
        logger.info("Returning content for '%s'", shortcut_name)
        return PlainTextResponse(value)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
