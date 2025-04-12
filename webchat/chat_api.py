#!/usr/bin/env python3-allemande

""" A simple chat API for use with the chat client. """

import os
import json
import time
import logging
import asyncio

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from pywebpush import webpush
import uvicorn
from deepmerge import always_merger

import chat
import ally_room
from ally_room import Room
import util
import settings


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
        room = util.sanitize_pathname(room)
    # TODO moderator status might depend on the room
    user = request.headers["X-Forwarded-User"]
    admin = user in settings.ADMINS
    mod = admin
    return JSONResponse({"user": user, "room": room, "admin": admin, "mod": mod})


@app.route("/x/post", methods=["POST"])
async def post(request):
    """Post a message to a room."""
    form = await request.form()
    room = form["room"]
    content = form["content"].strip()
    user = request.headers["X-Forwarded-User"]

    room = Room(name=room)

    try:
        exists = room.exists()
        room.write(user, content)

        # If the file was just created, we need to poke it again to get a response;
        # This is so that we don't trigger responses when moving files, checkout, and such.

        if not exists:
            await asyncio.sleep(0.2)
            room.touch()
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

    noclobber = request.query_params.get("noclobber") == "1"

    content = await request.body()
    content = content.decode()

    try:
        await ally_room.overwrite_file(user, path, content, delay=0.2, noclobber=noclobber)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=e.args[0]) from e
    return JSONResponse({"status": "success"})


@app.route("/x/upload", methods=["POST"])
async def upload(request):
    """File upload."""
    form = await request.form()
    room = form["room"]
    room = util.sanitize_pathname(room)
    file = form["file"]
    to_text = form.get("to_text", False)
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

    if op not in ["clear", "archive", "rotate", "clean"]:
        raise HTTPException(status_code=400, detail="Invalid operation.")

    room = Room(name=room)
    try:
        await room.clear(user, op)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=e.args[0]) from e
    return JSONResponse({})


@app.route("/x/undo", methods=["POST"])
async def undo(request):
    """Erase the previous n messages from a room."""
    form = await request.form()
    room = form["room"]
    n = form.get("n", "1")
    user = request.headers["X-Forwarded-User"]

    room = Room(name=room)
    try:
        room.undo(user, n=int(n))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=e.args[0]) from e
    return JSONResponse({})


@app.route("/x/settings", methods=["POST"])
async def settings(request):
    """Update user settings, including theme."""
    user = request.headers["X-Forwarded-User"]
    settings = await request.json()
    theme = settings.pop("theme", None)
    if theme:
        chat.set_user_theme(user, theme)
    if settings:
        raise HTTPException(status_code=400, detail="Invalid settings.")
    return JSONResponse({})


@app.route("/x/options", methods=["POST"])
async def options_set(request):
    """Update chat room options, including agent settings like context."""
    user = request.headers["X-Forwarded-User"]
    request = await request.json()
    room = Room(name=request["room"])
    old_options = room.get_options(user)
    new_options = request["options"]
    options = always_merger.merge(old_options, new_options)
    try:
        room.set_options(user, options)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=e.args[0]) from e
    return JSONResponse({})


@app.route("/x/options", methods=["GET"])
async def options_get(request):
    """Get chat room options, including agent settings like context. Also checks for a redirect."""
    # TODO validation: length, type, no unknown keys
    user = request.headers["X-Forwarded-User"]
    # get room from query param
    room = Room(name=request.query_params["room"])
    try:
        options = room.get_options(user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=e.args[0]) from e
    return JSONResponse(options)


@app.route("/x/last", methods=["GET"])
async def last(request):
    """Get last numbered chat room."""
    user = request.headers["X-Forwarded-User"]
    # get room from query param
    room_name = request.query_params["room"]
    room_name = util.sanitize_pathname(room_name)
    room = Room(name=room_name)
    logger.info("Getting last room number for %s", room_name)
    try:
        last = room.get_last_room_number(user)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=e.args[0]) from e
    return JSONResponse({"last": last})


@app.route("/x/move", methods=["POST"])
async def move(request):
    """
    Rename or move a file or dir to a new location.
    Expacts relative pathnames not room names or slash-terminated dir names.
    """
    user = request.headers["X-Forwarded-User"]
    # get source and dest from form data
    form = await request.form()
    source = form["source"]
    dest = form["dest"]
    try:
        ally_room.move_file(user, source, dest)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=e.args[0]) from e
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
