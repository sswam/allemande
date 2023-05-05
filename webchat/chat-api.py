#!/usr/bin/env python3

""" A simple chat API for use with the chat client. """

from pathlib import Path
import re

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
import uvicorn

import chat


ADMINS = ["sam"]
ROOMS = "rooms"
EXTENSION = ".bb"
ROOM_MAX_LENGTH = 100
ROOM_MAX_DEPTH = 10


async def http_exception(_request: Request, exc: HTTPException):
	""" Handle exceptions. """
	return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


exception_handlers = {
	HTTPException: http_exception,
}


app = Starlette(exception_handlers=exception_handlers)


@app.route("/x/whoami", methods=["GET", "POST"])
async def whoami(request):
	""" Return the user and whether they are an admin. """
	# TODO admin status might depend on the room
	# TODO sanitize the room
	user = request.headers.get('X-Forwarded-User', 'guest')
	admin = user in ADMINS
	return JSONResponse({"user": user, "admin": admin})


def sanitize_filename(f):
	""" Sanitize a filename, allowing most characters. """

	assert isinstance(f, str)
	assert "/" not in f

	# remove leading dots and whitespace:
	# don't want hidden files
	f = re.sub(r"^[.\s]+", "", f)

	# remove trailing dots and whitespace:
	# don't want confusion around file extensions
	f = re.sub(r"[.\s]+$", "", f)

	# squeeze whitespace
	f = re.sub(r"\s+", " ", f)

	return f


def ident(f):
	""" identity function """
	return f


def sanitize_pathname(room):
	""" Sanitize a pathname, allowing most characters. """

	# split into parts
	parts = room.split("/")

	# sanitize each part
	parts = map(sanitize_filename, parts)

	# remove empty parts
	parts = filter(ident, parts)

	if not parts:
		raise HTTPException(status_code=400, detail="Please enter the name of a room.")

	if len(parts) > ROOM_MAX_DEPTH:
		raise HTTPException(status_code=400, detail=f"The room is too deeply nested, max {ROOM_MAX_DEPTH} parts.")

	# join back together
	room = "/".join(parts)

	if len(room) > ROOM_MAX_LENGTH:
		raise HTTPException(status_code=400, detail=f"The room name is too long, max {ROOM_MAX_LENGTH} characters.")

	# check for control characters
	if re.search(r"[\x00-\x1F\x7F]", room):
		raise HTTPException(status_code=400, detail="The room name cannot contain control characters.")

	return room


def write_to_room(room, user, content):
	""" Write a message to a room. """
	assert isinstance(room, str)
	assert not room.startswith("/")
	assert not room.endswith("/")
	base_dir = Path(ROOMS).resolve()
	markdown_file = chat.safe_join(base_dir, room + EXTENSION)
	# html_file = chat.safe_join(base_dir, room+".html")
	user_tc = user.title()
	message = {"user": user_tc, "content": content}

	text = chat.message_to_text(message)
	dirname = Path(room).parent
	dirname.mkdir(parents=True, exist_ok=True)
	with markdown_file.open("a", encoding="utf-8") as f:
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
	room = sanitize_pathname(room)
	content = form["content"]
	user = request.headers['X-Forwarded-User']
	write_to_room(room, user, content)
	return JSONResponse({})


if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8000)
