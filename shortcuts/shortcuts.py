# File: /home/sam/allemande/shortcuts/shortcuts.py
import logging
import os
from starlette.applications import Starlette
from starlette.responses import RedirectResponse
from starlette.exceptions import HTTPException
from starlette.requests import Request

# --- Configuration ---
# It's good practice to declare variables at the top.
SHORTCUTS_DIR = "/var/www/shortcuts"
app = Starlette()

# Configure basic logging.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


def get_redirect_url(shortcut_name: str) -> str | None:
    """
    Safely reads the content of a shortcut file.

    Reads the file corresponding to the shortcut name. We use os.path.join
    to prevent directory traversal issues. The function returns the first
    line of the file, stripped of whitespace, or None if the file is not found.
    """
    # Sanitize input to prevent accessing files outside the intended directory.
    # This rejects any names containing '..' or '/'.
    if ".." in shortcut_name or "/" in shortcut_name:
        return None

    file_path = os.path.join(SHORTCUTS_DIR, shortcut_name)

    try:
        # Using `with` ensures the file is closed automatically.
        with open(file_path, "r", encoding="utf-8") as f:
            # Read the first line and strip any leading/trailing whitespace.
            url = f.readline().strip()
            return url if url else None
    except FileNotFoundError:
        return None


@app.route("/{shortcut_name:str}")
async def handle_redirect(request):
    """
    Main endpoint to handle a shortcut request.
    """
    shortcut_name = request.path_params["shortcut_name"]
    logging.info("Request for shortcut: %s", shortcut_name)
    target_url = get_redirect_url(shortcut_name)

    # Fail fast if the shortcut doesn't exist or the file is empty.
    if not target_url:
        logging.warning("Shortcut not found: %s", shortcut_name)
        raise HTTPException(status_code=404)

    logging.info("Redirecting '%s' -> '%s'", shortcut_name, target_url)
    # Issue a temporary (302) redirect.
    return RedirectResponse(target_url, status_code=302)


if __name__ == "__main__":
    import uvicorn
    # For production, you'd run this with a proper ASGI server like Uvicorn.
    # uvicorn redirect_service:app --host 127.0.0.1 --port 9090
    uvicorn.run(app, host="127.0.0.1", port=9090)
