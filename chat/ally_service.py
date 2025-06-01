import os
from pathlib import Path
import re

from starlette.requests import Request


def get_user(request: Request) -> str:
    """Get the user from the request headers."""
    user = request.headers["X-Forwarded-User"]
    # Attempt to decode the user header to UTF-8.
    try:
        user = user.encode('latin1').decode('utf-8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass
    return user


def add_mtime_to_resource_pathnames(html_string, chat_base_url):
    static_dir = Path(os.environ['ALLEMANDE_HOME']) / 'webchat' / 'static'

    def url_add_mtime(match):
        url_start = match.group(1)

        # Extract the full path after chat_base_url
        path_parts = match.group(2).split('/')

        # Split filename and extension
        base, ext = os.path.splitext(path_parts[-1])

        # if no ext, look for .js for abbreviated module import
        if not ext:
            path_parts[-1] += ".js"

        # Construct the full filepath under static dir
        filepath = static_dir.joinpath(*path_parts)

        if filepath.exists():
            # Get the last modified time
            mtime = int(filepath.stat().st_mtime)

            # Build new path with .mtime before extension
            new_filename = f"{base}.{mtime}{ext}"

            # Reconstruct full path, preserving any subdirectories
            path_parts[-1] = new_filename
            new_path = '/'.join(path_parts)
            return f'"{url_start}{new_path}"'

        return match.group(0)  # Return unchanged if file not found

    base_q = re.escape(chat_base_url)
    pattern = rf'"({base_q}/|chat:)([^"\s]+)"'
    return re.sub(pattern, url_add_mtime, html_string)
