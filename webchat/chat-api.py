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
VAPID_PRIVATE_KEY = os.environ["ALLYCHAT_WEBPUSH_VAPID_PRIVATE_KEY"]

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
	"""
	Write a message to a room.
	We don't convert to HTML here, a follower process does that.
	"""
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

	if op not in ["clear", "archive", "rotate"]:
		raise HTTPException(status_code=400, detail="Invalid operation.")

	room = chat.Room(name=room)
	admin = room.check_admin(user)
	if not admin:
		raise HTTPException(status_code=403, detail=f"You are not allowed to {op} this room.")

	room.clear(op)

	return JSONResponse({})


@app.route("/x/undo", methods=["POST"])
async def clear(request):
	""" Erase the previous n messages from a room. """
	form = await request.form()
	room = form["room"]
	n = form.get("n", "1")
	user = request.headers['X-Forwarded-User']

	room = chat.Room(name=room)
	admin = room.check_admin(user)
	if not admin:
		raise HTTPException(status_code=403, detail="You are not allowed to undo messages in this room.")
	room.undo(n=int(n))
	return JSONResponse({})


@app.route("/x/subscribe", methods=["POST"])
async def subscribe(request):
	""" Subscribe to push notifications. """
	data = await request.json()
	user_id = request.user.id

	# Store subscription in user settings file
	# TODO where?  maybe in among the rooms
	# It will be in a file used for other private settings too,
	# and likely YAML format not JSON.
	user_path = f"/var/allemande/users/{user_id}"
	os.makedirs(user_path, exist_ok=True)

	with open(f"{user_path}/push_subscription.json", "w") as f:
		json.dump(data["subscription"], f)

	return JSONResponse({"status": "success"})


async def send_push(user_id, message):
	""" Send a push notification to a user. """
	# TODO fix the path, and extract the subscription from the user settings file
	# Load user's subscription
	with open(f"/var/allemande/users/{user_id}/push_subscription.json") as f:
		subscription = json.load(f)

	vapid_claims = {
		"sub": "mailto:admin@allemande.ai",
		"exp": int(time.time()) + 12 * 3600,  # 12 hours from now
	}

	# Send encrypted push notification
	# Using webpush library for encryption handling
	webpush(
		subscription_info=subscription,
		data=message,
		vapid_private_key=VAPID_PRIVATE_KEY,
		vapid_claims=vapid_claims,
	)


# TODO implement the actual notifications when:
# - a message is posted to a watched room
# - user is invoked in a message, in any room to which they have access
#     - note that not every mention invokes a user
# - avoid sending notifications if the user is active in the room, somehow
#     - or delay them until we are sure the user didn't see the message


if __name__ == "__main__":
	uvicorn.run(app, host="127.0.0.1", port=8000)
