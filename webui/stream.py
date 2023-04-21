#!/usr/bin/env python3

""" stream.py: Watch a file and stream it to the browser like tail -f """

import sys
import logging
from pathlib import Path
import asyncio
import aiofiles
import aionotify
from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse, PlainTextResponse
import uvicorn

from starlette.routing import Convertor

app = Starlette()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

base_dir = Path(".").resolve()

FOLLOW_SLEEP = 0.1
FOLLOW_KEEPALIVE = 50


def sanitize_path(base_dir: Path, path: Path) -> Path:
	""" Return a safe path, or raise ValueError if the path is invalid or unsafe. """
	safe_path = base_dir.joinpath(path).resolve()
	if base_dir in safe_path.parents:
		return safe_path
	else:
		raise ValueError("Invalid or unsafe path provided.")


async def follow(file, keepalive=FOLLOW_KEEPALIVE, keepalive_string="\n"):
	""" Follow a file and yield new lines as they are added. """
	watcher = aionotify.Watcher()
	watcher.watch(file, aionotify.Flags.MODIFY)

	await watcher.setup(asyncio.get_event_loop())

	async with aiofiles.open(file, mode='r') as f:
		while True:
			while line := await f.readline():
				logger.info(f"sending line: {line}")
				yield line
			try:
				logger.info(f"waiting for file to change")
				event = await asyncio.wait_for(watcher.get_event(), timeout=keepalive)
			except asyncio.TimeoutError:
				logger.info(f"sending keepalive: {keepalive_string}")
				yield keepalive_string

	watcher.close()


@app.route("/stream/{path:path}", methods=["GET"])
async def stream(request):
	""" Stream a file to the browser, like tail -f """
	path = Path(request.path_params['path'])
	safe_path = sanitize_path(base_dir, path)

	media_type = "text/plain"
	keepalive_string = "\n"
	ext = safe_path.suffix
	if ext == ".html":
		media_type = "text/html"
		keepalive_string = "<script>online()</script>\n"

	logger.info(f"tail: {safe_path}")
	follower = follow(str(safe_path), keepalive_string=keepalive_string)
	return StreamingResponse(follower, media_type=media_type)


if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8000)
