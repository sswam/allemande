#!/usr/bin/env python3-allemande

""" A simple chat API for use with the chat client. """

import os
from pathlib import Path

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
import uvicorn

import chat


ADMINS = os.environ.get("ALLYCHAT_ADMINS", "").split()
ROOMS = "rooms"
EXTENSION = ".bb"


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
	form = await request.form()
	room = form.get("room")
	if room:
		room = chat.sanitize_pathname(room)
	# TODO moderator status might depend on the room
	user = request.headers.get('X-Forwarded-User', 'guest')
	admin = user in ADMINS
	mod = admin
	return JSONResponse({"user": user, "room": room, "admin": admin, "mod": mod})


def write_to_room(room, user, content):
	""" Write a message to a room. """
	assert isinstance(room, str)
	assert not room.startswith("/")
	assert not room.endswith("/")
	base_dir = Path(ROOMS).resolve()
	markdown_file = chat.safe_join(base_dir, room + EXTENSION)
	# html_file = chat.safe_join(base_dir, room+".html")
	dirname = Path(markdown_file).parent
	dirname.mkdir(parents=True, exist_ok=True)

	if content == "":
		# touch the markdown_file, to poke some attention
		markdown_file.touch()
		return

	if user == user.lower() or user == user.upper():
		user_tc = user.title()
	else:
		user_tc = user
	user_tc = user_tc.replace(".", "_")
	message = {"user": user_tc, "content": content}

	text = chat.message_to_text(message) + "\n"

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
	room = chat.sanitize_pathname(room)
	content = form["content"]
	user = request.headers['X-Forwarded-User']
	try:
		write_to_room(room, user, content)
	except PermissionError:
		raise HTTPException(status_code=403, detail="You are not allowed to post to this room.")
	return JSONResponse({})


if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8000)
