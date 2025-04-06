#!/usr/bin/env python3-allemande

"""
List directory contents with MIME types and icons.
"""

import os
import logging
from pathlib import Path
from typing import TextIO
import json
import mimetypes
import dataclasses
from typing import Any

from starlette.templating import Jinja2Templates

import chat
import ally_room
from ally_room import Access
from ally import debug
from util import sanitize_pathname, safe_join

logger = logging.getLogger(__name__)

mimetypes.init()


# File categorization
SYSTEM_TEXT_FILE_EXTS = ["m", "yml", "txt", "css", "js"]
MEDIA_FILE_EXTS = ["webm", "jpg"]

MIME_TYPE_ICONS = {
    # Main categories
    "inode/directory": "📁",  # Folders

    # Audio
    "audio/*": "🎵",

    # Video
    "video/*": "🎬",

    # Images
    "image/*": "🖼️",

    # Documents
    "application/pdf": "📄",
    "application/msword": "📄",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "📄",
    "text/plain": "📄",
    "text/markdown": "📄",
    "text/*": "📄",

    # Spreadsheets
    "application/vnd.ms-excel": "📊",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "📊",
    "text/csv": "📊",

    # Presentations
    "application/vnd.ms-powerpoint": "📽️",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "📽️",

    # Archives
    "application/zip": "📦",
    "application/x-rar-compressed": "📦",
    "application/x-7z-compressed": "📦",
    "application/x-tar": "📦",
    "application/gzip": "📦",

    # Code
    "text/x-python": "💻",
    "text/javascript": "💻",
    "text/html": "💻",
    "text/css": "💻",
    "application/json": "💻",
    "application/xml": "💻",
    "application/x-sh": "💻",

    # Fonts
    "font/*": "🔤",
    "application/font-sfnt": "🔤",
    "application/font-woff": "🔤",

    # Executables
    "application/x-executable": "⚙️",
    "application/x-mach-binary": "⚙️",
    "application/x-msdownload": "⚙️",

    # Unknown
    "application/octet-stream": "❓",

    # Special icons
    "text/x-allychat": "💬",  # a speech bubble
    "text/x-allychat-mission": "📜",  # a scroll
    "text/yaml": "⚙️",  # a gear
}

SPECIAL_TYPES = {
    "bb": "text/x-allychat",
    "m": "text/x-allychat-mission",
    "yml": "text/yaml",
}


@dataclasses.dataclass
class FolderInfo:
    user: str
    chat_base_url: str
    rooms_base_url: str


def get_mime_type_and_icon(path: Path) -> tuple[str, str]:
    """Get MIME type and icon for a file."""
    ext = path.suffix.lstrip(".").lower()

    # Handle directories
    if path.is_dir():
        mime_type = "inode/directory"

    # Special icons for certain file types
    else:
        mime_type = SPECIAL_TYPES.get(ext)

    # Get MIME type using python-magic
    if not mime_type:
        mime_type, _ = mimetypes.guess_type(str(path))
#         try:
#             mime_type = magic.from_file(str(path.suffix), mime=True)
#         except:
#             # Fallback to mimetypes library if magic fails
#             mime_type, _ = mimetypes.guess_type(str(path))

    if not mime_type:
        mime_type = "application/octet-stream"

    icon = MIME_TYPE_ICONS.get(mime_type)

    # Check for wildcard matches (e.g., "audio/*")
    if not icon:
        main_type = mime_type.split("/")[0] + "/*"
        icon = MIME_TYPE_ICONS.get(main_type, MIME_TYPE_ICONS["application/octet-stream"])

    return mime_type, icon


def get_dir_listing(path: Path, pathname: str, info: FolderInfo) -> list[dict[str, str]]:
    """Get directory listing with MIME types and icons."""
    items = [item for item in path.iterdir() if not item.name.startswith(".")]
    item_names = [item.name for item in items]
    listing = []

    pathname = pathname.strip("/")
    if pathname:
        pathname += "/"

    for item in items:
        mime_type, icon = get_mime_type_and_icon(item)
        ext = item.suffix.lstrip(".").lower()
        record = {
            "mime_type": mime_type,
            "icon": icon,
        }

        if item.is_dir():
            record.update(
                {
                    "name": item.name + "/",
                    "type": "folder",
                    "type_sort": 0,
                    "link": f"/#{pathname}{item.name}/",  # view dir
                }
            )
        elif ext == "bb":
            record.update(
                {
                    "name": item.stem,
                    "type": "bb",
                    "type_sort": 1,
                    "link": f"/#{pathname}{item.stem}",  # enter room
                }
            )
        elif ext == "html" and item.stem + ".bb" in item_names:
            # We don't want to show the rendered HTML file for a BB chat file
            continue
        elif ext in SYSTEM_TEXT_FILE_EXTS:
            record.update(
                {
                    "name": item.name,
                    "type": "file",
                    "type_sort": 10 + SYSTEM_TEXT_FILE_EXTS.index(ext),
                    "link": f"/#{pathname}{item.name}",  # edit file
                }
            )
        elif ext in MEDIA_FILE_EXTS:
            # Don't show media files for now.
            continue
            # record.update(
            #     {
            #         "name": item.name,
            #         "type": "file",
            #         "type_sort": 100 + MEDIA_FILE_EXTS.index(ext),
            #         "link": f"{info.rooms_base_url}/{pathname}{item.name}",
            #     }
            # )
        else:
            # Don't show random files for now.
            continue
            # record.update(
            #     {
            #         "name": item.name,
            #         "type": "file",
            #         "type_sort": 200,
            #         "link": f"{info.rooms_base_url}/{pathname}{item.name}",
            #     }
            # )

#        if not debug.profile_function(ally_room.check_access, info.user, pathname + item.name).value & Access.READ.value:
        if not ally_room.check_access(info.user, pathname + item.name).value & Access.READ.value:
            continue

        listing.append(record)

    return sorted(listing, key=lambda x: (x["type_sort"], x["name"].lower()))


def get_dir_listing_html(path: Path, pathname: str, info: FolderInfo, templates: Jinja2Templates = None, context: dict[str,Any] = None) -> str:
    """Get directory listing as HTML"""
    listing = get_dir_listing(path, pathname, info)

    html = []

    # HTML header
    if templates:
        html.append(templates.get_template("dir_header.html").render(context))

    # Generate HTML for directory listing
    html.append(f'<ul class="directory-listing">')
    for item in listing:
        html.append(f'''
            <li class="item-{item['type']}">
                <a href="{item['link']}">
                    <span class="icon" title="{item['mime_type']}">{item['icon']}</span>
                    <span class="name">{item['name']}</span>
                </a>
            </li>
        ''')
    html.append('</ul>')

    return "\n".join(html) + "\n"


def list_directory(
    ostream: TextIO,
    path: str = ".",
    user: str = "",
    json_output: bool = False,
    html_output: bool = False,
) -> None:
    """List directory contents with MIME types and icons."""
    try:
        pathname = sanitize_pathname(path)
        dir_path = safe_join(Path(".").resolve(), Path(pathname))

        if not dir_path.is_dir():
            raise ValueError(f"Not a directory: {path}")

        listing = get_dir_listing(dir_path, pathname, user)

        if json_output and html_output:
            raise ValueError("Cannot output both JSON and HTML")

        if json_output:
            json.dump(listing, ostream, indent=2)
            ostream.write("\n")
            return

        if html_output:
            ostream.write(get_dir_listing_html(dir_path, pathname, user))
            return

        for item in listing:
            ostream.write(f"{item['icon']} {item['name']}\n")

    except Exception as exc:
        logger.error("Error listing directory: %s", exc)
        raise


def setup_args(arg):
    """Set up command-line arguments."""
    arg("path", nargs="?", default=".", help="directory to list")
    arg("-u", "--user", help="user for access control")
    arg("-j", "--json", dest="json_output", action="store_true", help="output JSON format")
    arg("-H", "--html", dest="html_output", action="store_true", help="output HTML format")


if __name__ == "__main__":
    from ally import main

    main.go(list_directory, setup_args)
