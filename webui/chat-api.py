#!/usr/bin/env python3
from pathlib import Path
import asyncio
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
import uvicorn

import chat

app = Starlette()

ADMINS = ["sam"]
ROOMS = "rooms"

@app.route("/x/whoami", methods=["GET", "POST"])
async def whoami(request):
	# TODO admin might depend on the room
	user = request.headers['X-Forwarded-User']
	admin = user in ADMINS
	return JSONResponse({"user": user, "admin": admin})

def write_to_room(room, user, content):
	base_dir = Path(ROOMS).resolve()
	markdown_file = chat.safe_join(base_dir, room+".md")
	html_file = chat.safe_join(base_dir, room+".html")
	message = {"user": user, "content": content}

	text = chat.message_to_text(message)
	with markdown_file.open("a") as f:
		f.write(text)

	html = chat.message_to_html(message)
	with html_file.open("a") as f:
		f.write(html)

@app.route("/x/post", methods=["POST"])
async def post(request):
	form = await request.form()
	room = form["room"]
	content = form["content"]
	user = request.headers['X-Forwarded-User']
	write_to_room(room, user, content)
	return JSONResponse({"status": "okay"})

if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8000)
