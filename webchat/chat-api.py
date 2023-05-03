#!/usr/bin/env python3

""" A simple chat API for use with the chat client. """

from pathlib import Path
import asyncio
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
import uvicorn

import chat


ADMINS = ["sam"]
ROOMS = "rooms"
EXTENSION = ".bb"


app = Starlette()


@app.route("/x/whoami", methods=["GET", "POST"])
async def whoami(request):
	""" Return the user and whether they are an admin. """
	# TODO admin status might depend on the room
	user = request.headers.get('X-Forwarded-User', 'guest')
	admin = user in ADMINS
	return JSONResponse({"user": user, "admin": admin})


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
	content = form["content"]
	user = request.headers['X-Forwarded-User']
	write_to_room(room, user, content)
	return JSONResponse({"status": "okay"})


if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8000)
