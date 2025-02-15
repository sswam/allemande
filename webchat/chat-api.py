#!/usr/bin/env python3-allemande

""" A simple chat API for use with the chat client. """

import os
import json
import time
import logging

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from pywebpush import webpush
import uvicorn

import chat


VAPID_PRIVATE_KEY = os.environ["ALLYCHAT_WEBPUSH_VAPID_PRIVATE_KEY"]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def http_exception(_request: Request, exc: HTTPException):
    """Handle exceptions."""
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)



exception_handlers = {
    HTTPException: http_exception,
}


app = Starlette(exception_handlers=exception_handlers)
# app = Starlette(debug=True)  # Allow default exception handlers


@app.route("/x/whoami", methods=["GET", "POST"])
async def whoami(request):
    """Return the user and whether they are an admin."""
    form = await request.form()
    room = form.get("room")
    if room:
        room = chat.sanitize_pathname(room)
    # TODO moderator status might depend on the room
    user = request.headers["X-Forwarded-User"]
    admin = user in chat.ADMINS
    mod = admin
    return JSONResponse({"user": user, "room": room, "admin": admin, "mod": mod})


@app.route("/x/post", methods=["POST"])
async def post(request):
    """Post a message to a room."""
    form = await request.form()
    room = form["room"]
    content = form["content"]
    user = request.headers["X-Forwarded-User"]

    room = chat.Room(name=room)

    try:
        room.write(user, content)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=e.args[0]) from e
    return JSONResponse({})


@app.route("/x/put/{path:path}", methods=["PUT"])
async def put_file(request, path=""):
    """Edit a file in the room if user has admin access."""
    user = request.headers["X-Forwarded-User"]

    try:
        path = request.path_params["path"]
    except Exception as exc:
        logger.warning("Invalid path: %s", exc)
        raise

    content = await request.body()
    content = content.decode()

    try:
        await chat.overwrite_file(user, path, content, delay=0.1)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=e.args[0]) from e
    return JSONResponse({"status": "success"})


@app.route("/x/upload", methods=["POST"])
async def upload(request):
    """File upload."""
    form = await request.form()
    room = form["room"]
    room = chat.sanitize_pathname(room)
    file = form["file"]
    to_text = form.get(to_text, false)
    user = request.headers["X-Forwarded-User"]

    try:
        name, url, medium, markdown, task = await chat.upload_file(room, user, file.filename, file=file, to_text=to_text)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=e.args[0]) from e

    return JSONResponse({"name": name, "url": url, "medium": medium, "markdown": markdown}, background=task)


@app.route("/x/clear", methods=["POST"])
async def clear(request):
    """Clear a room."""
    form = await request.form()
    room = form["room"]
    op = form["op"]
    user = request.headers["X-Forwarded-User"]

    if op not in ["clear", "archive", "rotate"]:
        raise HTTPException(status_code=400, detail="Invalid operation.")

    room = chat.Room(name=room)
    room.clear(user, op)
    return JSONResponse({})


@app.route("/x/undo", methods=["POST"])
async def undo(request):
    """Erase the previous n messages from a room."""
    form = await request.form()
    room = form["room"]
    n = form.get("n", "1")
    user = request.headers["X-Forwarded-User"]

    room = chat.Room(name=room)
    room.undo(user, n=int(n))
    return JSONResponse({})


@app.route("/x/subscribe", methods=["POST"])
async def subscribe(request):
    """Subscribe to push notifications."""
    data = await request.json()
    user_id = request.user.id

    # Store subscription in user settings file
    # TODO where?  maybe in among the rooms
    # It will be in a file used for other private settings too,
    # and likely YAML format not JSON.
    user_path = f"/var/allemande/users/{user_id}"
    os.makedirs(user_path, exist_ok=True)

    with open(f"{user_path}/push_subscription.json", "w", encoding="utf-8") as f:
        json.dump(data["subscription"], f)

    return JSONResponse({"status": "success"})


async def send_push(user_id, message):
    """Send a push notification to a user."""
    # TODO fix the path, and extract the subscription from the user settings file
    # Load user's subscription
    with open(f"/var/allemande/users/{user_id}/push_subscription.json", encoding="utf-8") as f:
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
