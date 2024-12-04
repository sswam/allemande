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
import aiofiles

import chat
import video_compatible


ADMINS = os.environ.get("ALLYCHAT_ADMINS", "").split()
ROOMS = "rooms"
EXTENSION = ".bb"


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


def write_to_room(room, user, content):
	""" Write a message to a room. """
	assert isinstance(room, str)
	assert not room.startswith("/")
	assert not room.endswith("/")
	base_dir = Path(ROOMS).resolve()
	markdown_file = chat.safe_join(base_dir, room + EXTENSION)
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

	# We don't convert to HTML here, a follower process does that.


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


image_extensions = ['jpg', 'jpeg', 'png', 'gif', 'svg', 'webp']
audio_extensions = ['mp3', 'ogg', 'wav', 'flac', 'aac', 'm4a']
video_extensions = ['mp4', 'webm', 'ogv', 'avi', 'mov', 'flv', 'mkv']


async def save_uploaded_file(istream, file_path):
	""" Save an uploaded file. """
	chunk_size = 64 * 1024
	async with aiofiles.open(file_path, 'wb') as ostream:
		while chunk := await istream.read(chunk_size):
			await ostream.write(chunk)


async def upload_file(room, user, file):
	""" Upload a file to a room. """
	assert isinstance(room, str)
	assert not room.startswith("/")
	assert not room.endswith("/")
	base_dir = Path(ROOMS).resolve()
	room = chat.sanitize_pathname(room)
	parent_dir = (base_dir / room).parent
	parent_url = (Path("/")/room).parent

	name = chat.sanitize_filename(file.filename)
	stem, ext = os.path.splitext(name)

	i = 1
	suffix = ""
	while True:
		name = stem + suffix + ext
		file_path = parent_dir / name
		if not file_path.exists():
			break
		i += 1
		suffix = "_" + str(i)

	# TODO track which user uploaded which files?

	url = (parent_url / name).as_posix()

	logger.info(f"Uploading {name} to {room} by {user}: {file_path=} {url=}")

	await save_uploaded_file(file, str(file_path))

	task = None

	ext = ext.lower().lstrip(".")

	if ext in image_extensions:
		medium = "image"
	elif ext in audio_extensions:
		medium = "audio"
	elif ext in video_extensions:
		# webm can be audio or video
		result = await video_compatible.check(file_path)
		if result["video_codecs"]:
			medium = "video"
		else:
			medium = "audio"
		task = lambda: video_compatible.recode_if_needed(file_path, result=result, replace=True)
	else:
		medium = "file"

	if ext == "pdf":
		url += "#toolbar=0&navpanes=0&scrollbar=0"

	return name, url, medium, task


@app.route("/x/upload", methods=["POST"])
async def upload(request):
	""" File upload. """
	form = await request.form()
	room = form["room"]
	room = chat.sanitize_pathname(room)
	file = form["file"]
	user = request.headers['X-Forwarded-User']

	try:
		name, url, medium, task = await upload_file(room, user, file)
	except PermissionError:
		raise HTTPException(status_code=403, detail="You are not allowed to upload files to this room.")

	return JSONResponse({"name": name, "url": url, "medium": medium}, background=task)


if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8000)
