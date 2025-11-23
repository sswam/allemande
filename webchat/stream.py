#!/usr/bin/env python3-allemande

"""
Watch a chat file and stream it to the browser like tail -f.
Also serves directory listings.
"""

import os
import logging
from pathlib import Path
import asyncio
import re
import urllib

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import StreamingResponse, Response, JSONResponse, HTMLResponse
from starlette.exceptions import HTTPException
from starlette.templating import Jinja2Templates
import uvicorn

import aionotify

import atail
import akeepalive
import ally_room
from ally_room import Access
from util import sanitize_pathname, safe_join
import folder
from ally_service import get_user, add_mtime_to_resource_pathnames
import settings

from ally import cache
PATH_USERS = Path(os.environ["ALLEMANDE_USERS"]) / "users"


os.chdir(os.environ["ROOMS"])


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


VERSION = "0.1.2"
FOLLOW_KEEPALIVE = 5
HTML_KEEPALIVE = '<script class="event">online()</script>\n'
REWIND_STRING = '<script class="event">clear()</script>\n'
LOCK_FILE = ".lock"


BASE_DIR = Path(".").resolve()
TEMPLATES_DIR = os.environ.get("TEMPLATES")


templates: Jinja2Templates|None = None
lock_present = False
active_streams: dict[str, set[asyncio.Task]] = {}


def setup_templates():
    """Setup the templates directory"""
    global templates  # pylint: disable=global-statement
    if not TEMPLATES_DIR:
        logger.warning("No templates directory set")
        return
    templates = Jinja2Templates(directory=TEMPLATES_DIR)
    logger.debug("Using templates from %s", TEMPLATES_DIR)


def get_room_top_dir(pathname: str) -> str|None:
    """Check if pathname is a private room and return the owner username, or None."""
    if "/" in pathname:
        parts = pathname.split("/", 1)
        return parts[0]
    return None


def should_block_private_room(pathname: str, user: str) -> bool:
    """Check if a user should be blocked from accessing a private room when locked."""
    if not lock_present:
        return False

    top_dir = get_room_top_dir(pathname)
    if not top_dir:
        return False

    # Allow admins
    if user in settings.ADMINS:
        return False

    # Block if user matches top_dir
    return user == top_dir


async def watch_lock_file():
    """Watch for .lock file creation and removal."""
    global lock_present  # pylint: disable=global-statement

    lock_path = Path(LOCK_FILE)

    logger.info("watch_lock_file: start")

    # Initial check
    lock_present = lock_path.exists()
    if lock_present:
        logger.info("Lock file present at startup")
        await cancel_private_room_streams()

    watcher = aionotify.Watcher()
    watcher.watch(path=".", flags=aionotify.Flags.CREATE | aionotify.Flags.DELETE)

    await watcher.setup(asyncio.get_event_loop())

    try:
        while True:
            event = await watcher.get_event()
            if event is None:
                continue  # Shouldn't happen, but to fix pyrefly
            if event.name == LOCK_FILE:
                if event.flags & aionotify.Flags.CREATE:
                    logger.info("Lock file created, blocking private rooms")
                    lock_present = True
                    await cancel_private_room_streams()
                elif event.flags & aionotify.Flags.DELETE:
                    logger.info("Lock file removed, unblocking private rooms")
                    lock_present = False
    except asyncio.CancelledError:
        pass
    finally:
        watcher.close()


def is_private_room(pathname):
    """Is this a private room?"""
    users = cache.load(str(PATH_USERS)).strip().split("\n")
    top_dir = get_room_top_dir(pathname)
    if top_dir in users:
        return top_dir
    return None


async def cancel_private_room_streams():
    """Cancel all active streams to private rooms for non-admin, non-owner users."""
    for pathname, tasks in list(active_streams.items()):
        owner = is_private_room(pathname)
        if owner:
            # Cancel tasks for this private room
            for task in list(tasks):
                if not task.done():
                    logger.info("Cancelling stream for private room: %s", pathname)
                    task.cancel()


async def startup_event():
    """Startup event"""
    logger.info("Starting up...")
    setup_templates()
    asyncio.create_task(watch_lock_file())


async def shutdown_event():
    """Shutdown event"""
    logger.info("Shutting down...")
    # Cancel all active streams
    for tasks in active_streams.values():
        for task in tasks:
            if not task.done():
                task.cancel()


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

    follow_flag = not snapshot

    async with atail.AsyncTail(
        filename=file, wait_for_create=True, all_lines=True, follow=follow_flag, rewind=follow_flag, rewind_string=rewind_string, restart=follow_flag
    ) as queue1:
        async with akeepalive.AsyncKeepAlive(queue1, keepalive, timeout_return=keepalive_string) as queue2:
            try:
                while True:
                    line = await queue2.get()  # pyrefly: ignore
                    if "clear()" in line:
                        logger.info("line: %s", line)
                    queue2.task_done()  # pyrefly: ignore
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
        match = re.match(r'''
            (?:<head>(.*)</head>)?  # Optional head tag group with content
            \s*                     # Optional whitespace
            (?:<body>)?             # Optional opening body tag
            (.*)                    # Main content
            (?:</body>)?            # Optional closing body tag
        ''', extra_header, re.VERBOSE | re.DOTALL)
        if match is None:
            return header
        extra_head, extra_body = match.groups()
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
    snapshot = request.query_params.get("snapshot")

    user = get_user(request)

    try:
        pathname = request.path_params["path"]
        pathname = sanitize_pathname(pathname)
        path = safe_join(BASE_DIR, Path(pathname))
    except Exception as exc:
        logger.warning("Invalid path: %s", exc)
        raise

    # Handle symlink redirects for shortcuts
    if path.is_symlink():
        target = os.readlink(str(path))
        if target.startswith(("https://", "http://")):
            return Response(status_code=302, headers={"Location": target})
        elif target.startswith("/"):
            # Redirect relative to base URL, using the url library
            base_url_str = os.environ["ALLYCHAT_CHAT_URL"]
            base_url = urllib.parse.urlparse(base_url_str)
            redirect_url = urllib.parse.urljoin(f"{base_url.scheme}://{base_url.netloc}", target)
            return Response(status_code=302, headers={"Location": redirect_url})

    # Check if private room access should be blocked
    if should_block_private_room(pathname, user):
        logger.warning("Blocking access to private room %s for user %s (lock present)", pathname, user)
        raise HTTPException(status_code=502, detail="Service temporarily unavailable")

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

    # Track the stream task for potential cancellation
    current_task = asyncio.current_task()
    if current_task is not None:
        if pathname not in active_streams:
            active_streams[pathname] = set()
        active_streams[pathname].add(current_task)

    try:
        follower = follow(str(path), header=header, keepalive_string=keepalive_string, rewind_string=rewind_string, snapshot=snapshot)
        return StreamingResponse(follower, media_type=media_type)
    finally:
        # Clean up task tracking
        current_task = asyncio.current_task()
        if current_task is not None and pathname in active_streams:
            active_streams[pathname].discard(current_task)
            if not active_streams[pathname]:
                del active_streams[pathname]


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
