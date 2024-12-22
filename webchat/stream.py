#!/usr/bin/env python3-allemande

""" stream.py: Watch a chat file and stream it to the browser like tail -f """

import os
import logging
from pathlib import Path
import asyncio

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import StreamingResponse, Response
from starlette.exceptions import HTTPException
from starlette.templating import Jinja2Templates
import uvicorn

import chat
import atail
import akeepalive


os.chdir(os.environ["ROOMS"])


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


FOLLOW_KEEPALIVE = 50
HTML_KEEPALIVE = "<script>online()</script>\n"
REWIND_STRING = "<script>clear()</script>\n"


BASE_DIR = Path(".").resolve()
TEMPLATES_DIR = os.environ.get("TEMPLATES")


templates = None


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


async def http_exception(_request: Request, exc: HTTPException):
    """ Handle exceptions. """
    return Response(content=None, status_code=exc.status_code)


exception_handlers = {
    HTTPException: http_exception,
}


app = Starlette(on_startup=[startup_event], on_shutdown=[shutdown_event], exception_handlers=exception_handlers)


async def follow(file, head="", keepalive=FOLLOW_KEEPALIVE, keepalive_string="\n", rewind_string="\x0c\n"):
    """Follow a file and yield new lines as they are added."""

    # TODO read watch.log, then we won't have to create directories
    parent = Path(file).parent
    parent.mkdir(parents=True, exist_ok=True)

    if head:
        yield head

    async with atail.AsyncTail(filename=file, wait_for_create=True, all_lines=True, follow=True, rewind=True, rewind_string=rewind_string, restart=True) as queue1:
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


@app.route("/stream/{path:path}", methods=["GET"])
async def stream(request):
    """Stream a file to the browser, like tail -f"""
    global templates  # pylint: disable=global-statement, global-variable-not-assigned

    path = request.path_params["path"]
    path = chat.sanitize_pathname(path)
    path = Path(path)
    safe_path = chat.safe_join(BASE_DIR, path)

    media_type = "text/plain"
    head = ""
    keepalive_string = "\n"
    rewind_string = "\x0c\n"  # ^L / form feed / clear screen

    ext = safe_path.suffix

    if ext == ".html":
        media_type = "text/html"
        user = request.headers.get("X-Forwarded-User", "guest")
        if templates:
            context = {"request": request, "user": user}
            head = templates.get_template("room-head.html").render(context)
        keepalive_string = HTML_KEEPALIVE
        rewind_string = REWIND_STRING

    logger.info("tail: %s", safe_path)
    follower = follow(str(safe_path), head=head, keepalive_string=keepalive_string, rewind_string=rewind_string)
    return StreamingResponse(follower, media_type=media_type)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001)
