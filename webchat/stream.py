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
import re

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
import ally_room
from ally_room import Access
from util import sanitize_pathname, safe_join
import folder
from ally_service import get_user, add_mtime_to_resource_pathnames


os.chdir(os.environ["ROOMS"])


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


FOLLOW_KEEPALIVE = 5
HTML_KEEPALIVE = '<script class="event">online()</script>\n'
REWIND_STRING = '<script class="event">clear()</script>\n'


BASE_DIR = Path(".").resolve()
TEMPLATES_DIR = os.environ.get("TEMPLATES")


templates: Jinja2Templates = None


def setup_templates():
    """Setup the templates directory"""
    global templates  # pylint: disable=global-statement
    if not TEMPLATES_DIR:
        logger.warning("No templates directory set")
        return
    templates = Jinja2Templates(directory=TEMPLATES_DIR)
    logger.debug("Using templates from %s", TEMPLATES_DIR)


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


async def follow(file, header="", keepalive=FOLLOW_KEEPALIVE, keepalive_string="\n", rewind_string="\x0c\n", snapshot=False):
    """Follow a file and yield new lines as they are added."""

    # TODO read watch.log, then we won't have to create directories
    parent = Path(file).parent
    parent.mkdir(parents=True, exist_ok=True)

    if header:
        yield header

    follow = not snapshot

    async with atail.AsyncTail(
        filename=file, wait_for_create=True, all_lines=True, follow=follow, rewind=follow, rewind_string=rewind_string, restart=follow
    ) as queue1:
        async with akeepalive.AsyncKeepAlive(queue1, keepalive, timeout_return=keepalive_string) as queue2:
            try:
                while True:
                    line = await queue2.get()
                    logger.debug("line: %s", line)
                    queue2.task_done()
                    if line is None:
                        break
                    yield line
            except asyncio.CancelledError:
                pass


def try_loading_extra_header(path, header):
    """
    Load an extra header from a file if it exists.
    I'm not sure what this was for, not currently in use.
    """
    extra_header_path = path.with_suffix(".h.html")

    if extra_header_path.exists():
        extra_header = extra_header_path.read_text()
        extra_head, extra_body = re.match(r'''
            (?:<head>(.*)</head>)?  # Optional head tag group with content
            \s*                     # Optional whitespace
            (?:<body>)?             # Optional opening body tag
            (.*)                    # Main content
            (?:</body>)?            # Optional closing body tag
        ''', extra_header, re.VERBOSE | re.DOTALL).groups()
        if extra_head and "</head>" in header:
            header = header.replace("</head>", extra_head + "</head>")
        else:
            header += extra_head or ""
        if extra_body and "<body>" in header:
            header = header.replace("<body>", "<body>" + extra_body)
        else:
            header += extra_body

    return header


@app.route("/stream/", methods=["GET"])
@app.route("/stream/{path:path}", methods=["GET"])
async def stream(request, path=""):
    """Stream a file to the browser, like tail -f"""
    global templates  # pylint: disable=global-statement, global-variable-not-assigned
    snapshot = request.query_params.get("snapshot")

    user = get_user(request)

    try:
        pathname = request.path_params["path"]
        pathname = sanitize_pathname(pathname)
        path = safe_join(BASE_DIR, Path(pathname))
    except Exception as exc:
        logger.warning("Invalid path: %s", exc)
        raise

    rooms_base_url = str(request.base_url).rstrip("/")
    chat_base_url = rooms_base_url.replace("rooms", "chat")
    login_base_url = rooms_base_url.replace("rooms.", "")
    info = folder.FolderInfo(user=user, chat_base_url=chat_base_url, rooms_base_url=rooms_base_url, login_base_url=login_base_url)

    if not ally_room.check_access(user, pathname).value & Access.READ.value:
        raise HTTPException(status_code=404, detail="Not found")

    # readlink $ALLEMANDE_USERS/$user/theme.css
    theme_symlink = Path(os.environ["ALLEMANDE_USERS"], user, "theme.css")
    theme = theme_symlink.readlink().stem if os.path.islink(theme_symlink) else "default"

    room_path = re.sub(r"\.html$", "", pathname)

    context = {"user": user, "login_base_url": info.login_base_url, "chat_base_url": info.chat_base_url, "rooms_base_url": info.rooms_base_url, "theme": theme, "room": room_path}

    logger.info("context %r", context)

    # folder listings
    if path.is_dir():
        want_json = request.query_params.get('json') == '1'
        if want_json:
            return JSONResponse(folder.get_dir_listing(path, pathname, info))
        return HTMLResponse(folder.get_dir_listing_html(path, pathname, info, templates, context))

    media_type = "text/plain"
    header = ""
    keepalive_string = "\n"
    rewind_string = "\x0c\n"  # ^L / form feed / clear screen

    ext = path.suffix

    if ext == ".html":
        media_type = "text/html"
        if templates:
            header = templates.get_template("room_header.html").render(context)
        header = try_loading_extra_header(path, header)
        header = add_mtime_to_resource_pathnames(header, info.chat_base_url)
        keepalive_string = HTML_KEEPALIVE
        rewind_string = REWIND_STRING

    logger.debug("tail: %s", path)
    follower = follow(str(path), header=header, keepalive_string=keepalive_string, rewind_string=rewind_string, snapshot=snapshot)
    return StreamingResponse(follower, media_type=media_type)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
