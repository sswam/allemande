#!/usr/bin/env python3-allemande

""" A simple chat API for use with the chat client. """

import os
from pathlib import Path
import logging

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
import uvicorn

import chat


ADMINS = os.environ.get("ALLYCHAT_ADMINS", "").split()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def http_exception(_request: Request, exc: HTTPException):
	""" Handle exceptions. """
	return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


exception_handlers = {
	HTTPException: http_exception,
}


app = Starlette(exception_handlers=exception_handlers)


# TODO not currently using this, but it could be useful for extra info that's not in the cookie
@app.route("/x/whoami", methods=["GET", "POST"])
async def whoami(request):
	""" Return the user and whether they are an admin. """
	form = await request.form()
	room = form.get("room")
	if room:
		room = chat.sanitize_pathname(room)
	# TODO moderator status might depend on the room
	user = request.headers.get('X-Forwarded-User', 'guest')
	admin = user in ADMINS
	mod = admin
	return JSONResponse({"user": user, "room": room, "admin": admin, "mod": mod})


def write_to_room(room_name, user, content):
	""" Write a message to a room. """

	room = chat.Room(name=room_name)

	if content == "":
		# touch the markdown_file, to poke some attention
		room.touch()
		return

	if user == user.lower() or user == user.upper():
		user_tc = user.title()
	else:
		user_tc = user
	user_tc = user_tc.replace(".", "_")
	message = {"user": user_tc, "content": content}

	text = chat.message_to_text(message) + "\n"

	room.append(text)

	# We don't convert to HTML here, a follower process does that.


@app.route("/x/post", methods=["POST"])
async def post(request):
	""" Post a message to a room. """
	form = await request.form()
	room = form["room"]
	content = form["content"]
	user = request.headers['X-Forwarded-User']
	try:
		write_to_room(room, user, content)
	except PermissionError:
		raise HTTPException(status_code=403, detail="You are not allowed to post to this room.")
	return JSONResponse({})


@app.route("/x/upload", methods=["POST"])
async def upload(request):
	""" File upload. """
	form = await request.form()
	room = form["room"]
	room = chat.sanitize_pathname(room)
	file = form["file"]
	user = request.headers['X-Forwarded-User']

	try:
		name, url, medium, markdown, task = await chat.upload_file(room, user, file.filename, file=file)
	except PermissionError:
		raise HTTPException(status_code=403, detail="You are not allowed to upload files to this room.")

	return JSONResponse({"name": name, "url": url, "medium": medium, "markdown": markdown}, background=task)


@app.route("/x/clear", methods=["POST"])
async def clear(request):
	""" Clear a room. """
	form = await request.form()
	room = form["room"]
	op = form["op"]
	user = request.headers['X-Forwarded-User']

	if op not in ["clear", "rotate"]:
		raise HTTPException(status_code=400, detail="Invalid operation.")

	room = chat.Room(name=room)
	admin = room.check_admin(user)
	if not admin:
		raise HTTPException(status_code=403, detail="You are not allowed to clear this room.")
	room.clear(rotate = op == "rotate")
	return JSONResponse({})


if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8000)
