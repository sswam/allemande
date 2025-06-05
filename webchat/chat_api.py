#!/usr/bin/env python3-allemande

""" A simple chat API for use with the chat client. """

import os
import json
import time
import logging
import asyncio
from typing import Any

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.exceptions import HTTPException
from pywebpush import webpush
import uvicorn
from deepmerge import always_merger
import geoip2.database
import geoip2.errors

import chat
import ally_room
from ally_room import Room
import util
import settings
from ally_service import get_user


VAPID_PRIVATE_KEY = os.environ["ALLYCHAT_WEBPUSH_VAPID_PRIVATE_KEY"]
ALLEMANDE_DOMAIN = os.environ["ALLEMANDE_DOMAIN"]
GEOIP_DB_PATH = os.environ.get("ALLYCHAT_GEOIP_DB_PATH", "/var/lib/GeoIP/GeoLite2-City.mmdb")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize GeoIP reader once at startup
try:
    geoip_reader = geoip2.database.Reader(GEOIP_DB_PATH)
except FileNotFoundError:
    logger.warning("GeoIP database not found at %s", GEOIP_DB_PATH)
    geoip_reader = None
except Exception as e:  # pylint: disable=broad-except
    logger.error("Failed to initialize GeoIP reader: %s", e)
    geoip_reader = None


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
    user = get_user(request)
    admin = user in settings.ADMINS
    mod = admin
    return JSONResponse({"user": user, "room": room, "admin": admin, "mod": mod})


@app.route("/x/post", methods=["POST"])
async def post(request):
    """Post a message to a room."""
    form = await request.form()
    room = form["room"]
    content = form["content"].strip()
    user = get_user(request)

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
    user = get_user(request)

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
    user = get_user(request)

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
    user = get_user(request)

    if op not in ["clear", "archive", "rotate", "clean", "render"]:
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
    user = get_user(request)

    room = Room(name=room)
    try:
        await room.undo(user, n=int(n))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=e.args[0]) from e
    return JSONResponse({})


@app.route("/x/settings", methods=["POST"])
async def settings(request):
    """Update user settings, including theme."""
    user = get_user(request)
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
    user = get_user(request)
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
    user = get_user(request)
    # get room from query param
    room = Room(name=request.query_params["room"])
    try:
        options = room.get_options(user)
    except PermissionError as e:
        logger.info("PermissionError: %r", e)
        raise HTTPException(status_code=403, detail=e.args[0]) from e
    return JSONResponse(options)


@app.route("/x/last", methods=["GET"])
async def last(request):
    """Get last numbered chat room."""
    user = get_user(request)
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
    user = get_user(request)
    # get source and dest from form data
    form = await request.form()
    source = form["source"]
    dest = form["dest"]
    try:
        ally_room.move_file(user, source, dest)
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=e.args[0]) from e
    except ValueError as e:
        raise HTTPException(status_code=409, detail=e.args[0]) from e
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
        "sub": f"mailto:admin@{ALLEMANDE_DOMAIN}",
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

@app.route("/x/geoip", methods=["GET"])
async def geoip(request: Request):
    """Look up GeoIP info for an IP address."""
    if not geoip_reader:
        raise HTTPException(status_code=503, detail="GeoIP service not available")

    # First try to get IP from query parameters
    ip = request.query_params.get("ip")

    # If no IP provided in query, try to get it from headers
    if not ip:
        for header in ["X-Forwarded-For", "X-Real-IP"]:
            if header_value := request.headers.get(header):
                ip = header_value.split(',')[0].strip()
                break

    if not ip:
        raise HTTPException(status_code=400, detail="Could not determine IP address")

    try:
        response = geoip_reader.city(ip)
        return JSONResponse({
            "country": response.country.iso_code,
            "city": response.city.name,
            "location": {
                "latitude": response.location.latitude,
                "longitude": response.location.longitude
            }
        })
    except geoip2.errors.AddressNotFoundError:
        raise HTTPException(status_code=404, detail="IP address not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid IP address")
    except Exception as e:  # pylint: disable=broad-except
        logger.error("GeoIP lookup failed: %s", e)
        raise HTTPException(status_code=500, detail="GeoIP lookup failed")


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
