#!/usr/bin/env python3

""" stream.py: Watch a file and stream it to the browser like tail -f """

import sys
import logging
from pathlib import Path
import asyncio
import json
import re

import aiofiles
import aionotify
from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse, PlainTextResponse
import uvicorn
from starlette.templating import Jinja2Templates

import chat
import atail
import akeepalive


app = Starlette()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

base_dir = Path(".").resolve()

templates = Jinja2Templates(directory="templates")

FOLLOW_KEEPALIVE = 50

HTML_KEEPALIVE = "<script>online()</script>\n"


async def follow(file, head="", keepalive=FOLLOW_KEEPALIVE, keepalive_string="\n"):
	""" Follow a file and yield new lines as they are added. """

	if head:
		yield head

	tail = atail.AsyncTail(filename=file, wait_for_create=True, all_lines=True, follow=True, rewind=True).run()
	tail2 = akeepalive.AsyncKeepAlive(tail, keepalive, timeout_return=keepalive_string).run()

	async for line in tail2:
		yield line


@app.route("/stream/{path:path}", methods=["GET"])
async def stream(request):
	""" Stream a file to the browser, like tail -f """
	path = Path(request.path_params['path'])
	safe_path = chat.safe_join(base_dir, path)

	media_type = "text/plain"
	head = ""
	keepalive_string = "\n"
	ext = safe_path.suffix
	if ext == ".html":
		media_type = "text/html"
		user = request.headers.get('X-Forwarded-User', 'guest')
		context = {
			"request": request,
			"user": user
		}
		head = templates.get_template("room-head.html").render(context)
		keepalive_string = HTML_KEEPALIVE

	logger.info(f"tail: {safe_path}")
	follower = follow(str(safe_path), head=head, keepalive_string=keepalive_string)
	return StreamingResponse(follower, media_type=media_type)


if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8001)
