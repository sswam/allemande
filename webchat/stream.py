#!/usr/bin/env python3-allemande

"""
Watch a chat file and stream it to the browser like tail -f.
Also serves directory listings.
"""

import os
import logging
from pathlib import Path
import asyncio
from typing import Any
import dataclasses

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import StreamingResponse, Response, JSONResponse, HTMLResponse
from starlette.exceptions import HTTPException
from starlette.templating import Jinja2Templates
from starlette.types import Scope, Receive, Send
import uvicorn
import mimetypes
# import magic

import atail
import akeepalive
import chat
from chat import Access


os.chdir(os.environ["ROOMS"])


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


FOLLOW_KEEPALIVE = 50
HTML_KEEPALIVE = "<script>online()</script>\n"
REWIND_STRING = "<script>clear()</script>\n"


BASE_DIR = Path(".").resolve()
TEMPLATES_DIR = os.environ.get("TEMPLATES")


templates = None


mimetypes.init()


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
}


SPECIAL_TYPES = {
    "bb": "text/x-allychat",
    "m": "text/x-allychat-mission",
}


@dataclasses.dataclass
class Info:
    user: str
    chat_base_url: str
    rooms_base_url: str


def setup_templates():
    """Setup the templates directory"""
    global templates  # pylint: disable=global-statement
    if not TEMPLATES_DIR:
        logger.warning("No templates directory set")
        return
    templates = Jinja2Templates(directory=TEMPLATES_DIR)
    logger.info("Using templates from %s", TEMPLATES_DIR)


async def startup_event():
    """Startup event"""
    logger.info("Starting up...")
    setup_templates()


async def shutdown_event():
    """Shutdown event"""
    logger.info("Shutting down...")


async def http_exception(_request: Request, exc: HTTPException) -> Response:
    """Handle exceptions."""
    return Response(content=None, status_code=exc.status_code)


exception_handlers = {
    HTTPException: http_exception,
}


app = Starlette(
    on_startup=[startup_event],
    on_shutdown=[shutdown_event],
    exception_handlers=exception_handlers,  # type: ignore
)


async def follow(file, head="", keepalive=FOLLOW_KEEPALIVE, keepalive_string="\n", rewind_string="\x0c\n"):
    """Follow a file and yield new lines as they are added."""

    # TODO read watch.log, then we won't have to create directories
    parent = Path(file).parent
    parent.mkdir(parents=True, exist_ok=True)

    if head:
        yield head

    async with atail.AsyncTail(
        filename=file, wait_for_create=True, all_lines=True, follow=True, rewind=True, rewind_string=rewind_string, restart=True
    ) as queue1:
        async with akeepalive.AsyncKeepAlive(queue1, keepalive, timeout_return=keepalive_string) as queue2:
            try:
                while True:
                    line = await queue2.get()
                    if line is None:
                        break
                    yield line
                    queue2.task_done()
            except asyncio.CancelledError:
                pass


def get_mime_type_and_icon(path: str) -> str:
    path = Path(path)

    ext = path.suffix.lstrip('.').lower()

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
        main_type = mime_type.split('/')[0] + "/*"
        icon = MIME_TYPE_ICONS.get(main_type, MIME_TYPE_ICONS["application/octet-stream"])

    logger.warning("Name: %s, MIME type: %s, icon: %s", path.name, mime_type, icon)

    return mime_type, icon


def get_dir_listing(abs_path: Path, path: str, info: Info) -> list[dict[str, str]]:
    """Get directory listing for a path"""
    items = [item for item in abs_path.iterdir() if not item.name.startswith('.')]
    item_names = [item.name for item in items]

    listing = []

    path = path.lstrip("/")

    for item in items:
        mime_type, icon = get_mime_type_and_icon(item)
        record = {
            "mime_type": mime_type,
            "icon": icon,
        }
        if item.is_dir():
            record.update({
                "name": item.name + "/",
                "type": "folder",
                "type_sort": 0,
                "link": f"/#{path}/{item.name}/",
            })
        elif item.suffix == '.bb':
            record.update({
                "name": item.stem,
                "type": "bb",
                "type_sort": 1,
                "link": f"/#{path}/{item.stem}",
            })
        elif item.suffix == '.html' and item.stem + ".bb" in item_names:
            # We don't want to show the rendered HTML file for a BB chat file
            continue
        else:
            logger.warning("Path: %s, Name: %s, Suffix: %s", path, item.name, item.suffix)
            record.update({
                "name": item.name,
                "type": "file",
                "type_sort": 2,
                "link": f"{info.rooms_base_url}/{path}/{item.name}",
            })
        listing.append(record)

    return sorted(listing, key=lambda x: (x['type_sort'], x['name'].lower()))


def get_dir_listing_response(safe_path: Path, path: str, info: Info, json: bool) -> Response:
    """Get directory listing response, either JSON or HTML"""
    global templates  # pylint: disable=global-statement, global-variable-not-assigned

    listing = get_dir_listing(safe_path, path, info)

    if json:
        return JSONResponse(listing)

    html = []

    # HTML header
    if templates:
        context = {"user": info.user, "chat_base_url": info.chat_base_url}
        html.append(templates.get_template("dir-head.html").render(context))

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

    return HTMLResponse('\n'.join(html))


@app.route("/stream/", methods=["GET"])
@app.route("/stream/{path:path}", methods=["GET"])
async def stream(request, path=""):
    """Stream a file to the browser, like tail -f"""
    global templates  # pylint: disable=global-statement, global-variable-not-assigned

    user = request.headers.get("X-Forwarded-User", "guest")

    try:
        pathname = request.path_params["path"]
        pathname = chat.sanitize_pathname(pathname)
        path = chat.safe_join(BASE_DIR, Path(pathname))
    except Exception as exc:
        logger.warning("Invalid path: %s", exc)
        raise

    rooms_base_url = str(request.base_url).rstrip("/")
    chat_base_url = rooms_base_url.replace("rooms", "chat")
    info = Info(user=user, chat_base_url=chat_base_url, rooms_base_url=rooms_base_url)

    if not chat.check_access(user, pathname, path).value & Access.READ.value:
        raise HTTPException(status_code=404, detail="Not found")

    if path.is_dir():
        want_json = request.query_params.get('json') == '1'
        return get_dir_listing_response(path, pathname, info, json=want_json)

    media_type = "text/plain"
    head = ""
    keepalive_string = "\n"
    rewind_string = "\x0c\n"  # ^L / form feed / clear screen

    ext = path.suffix

    if ext == ".html":
        media_type = "text/html"
        if templates:
            context = {"user": user, "chat_base_url": info.chat_base_url}
            head = templates.get_template("room-head.html").render(context)
        keepalive_string = HTML_KEEPALIVE
        rewind_string = REWIND_STRING

    logger.info("tail: %s", path)
    follower = follow(str(path), head=head, keepalive_string=keepalive_string, rewind_string=rewind_string)
    return StreamingResponse(follower, media_type=media_type)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
