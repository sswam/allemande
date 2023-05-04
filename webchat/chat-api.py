#!/usr/bin/env python3

""" A simple chat API for use with the chat client. """

from pathlib import Path
import asyncio
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
import uvicorn
import re

import chat


ADMINS = ["sam"]
ROOMS = "rooms"
EXTENSION = ".bb"


async def http_exception(request: Request, exc: HTTPException):
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)

exception_handlers = {
    HTTPException: http_exception,
}


app = Starlette(exception_handlers=exception_handlers)


@app.route("/x/whoami", methods=["GET", "POST"])
async def whoami(request):
	""" Return the user and whether they are an admin. """
	# TODO admin status might depend on the room
	user = request.headers.get('X-Forwarded-User', 'guest')
	admin = user in ADMINS
	return JSONResponse({"user": user, "admin": admin})


def validate_room(room):
	return re.match(r"^[a-z0-9_-]+$", room)


def write_to_room(room, user, content):
	""" Write a message to a room. """
	base_dir = Path(ROOMS).resolve()
	markdown_file = chat.safe_join(base_dir, room + EXTENSION)
	html_file = chat.safe_join(base_dir, room+".html")
	user_tc = user.title()
	message = {"user": user_tc, "content": content}

	text = chat.message_to_text(message)
	with markdown_file.open("a") as f:
		f.write(text)

	# TODO don't convert to HTML here, a follower process will do that

#	html = chat.message_to_html(message)
#	with html_file.open("a") as f:
#		f.write(html)


@app.route("/x/post", methods=["POST"])
async def post(request):
	""" Post a message to a room. """
	form = await request.form()
	room = form["room"]
	if not validate_room(room):
		raise HTTPException(status_code=400, detail="Invalid room name")
	content = form["content"]
	user = request.headers['X-Forwarded-User']
	write_to_room(room, user, content)
	return JSONResponse({})


if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8000)
