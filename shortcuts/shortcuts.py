import logging
import os
from pathlib import Path
from urllib.parse import urljoin

from starlette.applications import Starlette
from starlette.responses import RedirectResponse, PlainTextResponse
from starlette.exceptions import HTTPException

SHORTCUTS_DIR = Path(os.environ["ALLEMANDE_HOME"])/"s"

app = Starlette()

# Configure basic logging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def get_content_or_url(shortcut_name: str) -> tuple[str, str] | None:
    """
    Safely reads the content or URL for a shortcut.

    Checks if the path is a regular file or symlink within the shortcuts dir.
    For regular files, returns ('content', file_content).
    For symlinks, returns ('redirect', target_url), handling relative URLs.
    Returns None if not found or invalid.
    """
    file_path = SHORTCUTS_DIR / shortcut_name
    try:
        resolved = file_path.resolve()
        if not resolved.is_relative_to(SHORTCUTS_DIR):
            return None
    except (OSError, RuntimeError):
        return None

    if resolved.is_file() and not resolved.is_symlink():
        # Regular file: return content
        try:
            with open(resolved, "r", encoding="utf-8") as f:
                content = f.read()
            return ('content', content)
        except (OSError, IOError):
            return None
    elif resolved.is_symlink():
        # Symlink: get URL and handle relative
        link_target = os.readlink(str(resolved))
        site_url = os.environ["ALLEMANDE_SITE_URL"]
        base_path = "/s/" + shortcut_name
        if not base_path.endswith('/'):
            base_path += '/'
        base_url = site_url + base_path
        url = urljoin(base_url, link_target)
        return ('redirect', url)
    else:
        return None


@app.route("/{shortcut_name:str}")
async def handle_redirect(request):
    """
    Main endpoint to handle a shortcut request.
    """
    shortcut_name = request.path_params["shortcut_name"]
    logging.info("Request for shortcut: %s", shortcut_name)
    result = get_content_or_url(shortcut_name)

    # Fail fast if not found
    if result is None:
        logging.warning("Shortcut not found: %s", shortcut_name)
        raise HTTPException(status_code=404)

    rtype, value = result
    if rtype == 'redirect':
        logging.info("Redirecting '%s' -> '%s'", shortcut_name, value)
        # Issue a temporary (302) redirect.
        return RedirectResponse(value, status_code=302)
    elif rtype == 'content':
        logging.info("Returning content for '%s'", shortcut_name)
        return PlainTextResponse(value)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
