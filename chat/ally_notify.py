#!/usr/bin/env python3-allemande

import os
import sys
import logging
import json
import asyncio
from pathlib import Path
from util import safe_join, ally_path

from pywebpush import webpush, WebPushException

from settings import ALLEMANDE_DOMAIN, PATH_USERS_DIR, PATH_ROOMS
from ally.cache import cache  # type: ignore # pylint: disable=wrong-import-order


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


VAPID_PRIVATE_KEY = os.environ["ALLYCHAT_WEBPUSH_VAPID_PRIVATE_KEY"]


def subs_path(user):
    return PATH_USERS_DIR / user / "push_subscriptions.json"


def load_subs(user):
    try:
        with open(subs_path(user), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_subs(user, subs):
    with open(subs_path(user), "w", encoding="utf-8") as f:
        json.dump(subs, f, indent=2)


def subscribe(user, sub):
    subs = load_subs(user)
    subs[sub["endpoint"]] = sub
    save_subs(user, subs)


def unsubscribe(user, endpoint):
    subs = load_subs(user)
    subs.pop(endpoint, None)
    save_subs(user, subs)


def send_one(subscription, message, room):
    """Synchronous; run via asyncio.to_thread."""
    data = json.dumps({"body": message, "room": room})  # , "url": ""})
    webpush(
        subscription_info=subscription,
        data=data,
        vapid_private_key=VAPID_PRIVATE_KEY,
        vapid_claims={"sub": f"mailto:admin@{ALLEMANDE_DOMAIN}"},
    )


async def send_push(user, message, room):
    subs = load_subs(user)
    if not subs:
        logger.warning("No subscriptions found for %s.", user)
    dead = []
    for endpoint, sub in subs.items():
        try:
            # XXX we might make a lot of threads, could be better to run one thread for sending notifications to all users
            await asyncio.to_thread(send_one, sub, message, room)
        except WebPushException as e:
            logger.error("Push failed for %s: %s", user, e)
            if e.response is not None and e.response.status_code in (404, 410):
                dead.append(endpoint)
    if dead:
        for ep in dead:
            del subs[ep]
        save_subs(user, subs)
        logger.warning("Removed %s dead subscription(s).", len(dead))


def notify_file_path(room_path):
    if room_path.endswith("/"):
        return room_path + ".notify"
    path = Path(room_path)
    return str(path.parent / ("." + path.name + ".notify"))


def notify_get(user: str, room: str) -> tuple[str, str]:
    """
    Check .{room}.notify, .notify and parent .notify files
    Returns:
    (specific, inherited): The setting for this specific room (may be "none"),
        and the inherited setting from a parent (may be "none")
    """
    room_path = ally_path(room)
    specific = "none"
    inherited = "none"

    # Check the specific room first
    notify_file = notify_file_path(room_path)
    data = cache.load(notify_file, fmt="yaml") or {}
    specific = data.get(user, "none")

    # Walk up the parent directories for inherited setting
    while True:
        room_path = str(Path(room_path).parent) + "/"
        if not room_path.startswith(str(PATH_ROOMS)):
            break
        notify_file = notify_file_path(room_path)
        data = cache.load(notify_file, fmt="yaml") or {}
        inherited = data.get(user, "none")
        if inherited != "none":
            break

    return specific, inherited


def notify_who(room: str) -> list[tuple[str, str]]:
    """
    Given a room, returns a list of (user, effective) tuples for all users
    with any notification setting for this room or inherited from parents.
    Specific settings override inherited; among inherited, closest parent wins.
    """
    room_path = ally_path(room)
    accumulated = {}

    # Walk from room up through parents, collecting settings
    # We go bottom-up so closer settings take priority (first seen wins)
    current_path = room_path
    while True:
        notify_file = notify_file_path(current_path)
        data = cache.load(notify_file, fmt="yaml") or {}
        for user_id, setting in data.items():
            if user_id not in accumulated:
                accumulated[user_id] = setting

        current_path = str(Path(current_path).parent) + "/"
        if not current_path.startswith(str(PATH_ROOMS)):
            break

    return [(user_id, setting) for user_id, setting in accumulated.items()]


def notify_set(user: str, room: str, setting: str) -> str:
    """
    Save specific notification setting in .{room}.notify or .notify for a folder.
    Lock around this if any chance of concurrency. Shouldn't be.
    """
    if setting not in ["none", "me", "all", "off"]:
        raise ValueError("notify_set: setting must be none, me, all, or off")

    room_path = ally_path(room)
    notify_file = notify_file_path(room_path)

    data = cache.load(notify_file, fmt="yaml") or {}
    if setting != "none":
        data[user] = setting
    else:
        data.pop(user, None)

    # Also save in users list of all watches, by room

    user_watches = PATH_USERS_DIR / user / "notify.yml"
    l = len(str(PATH_ROOMS)) + 1
    room1 = room_path[l:]

    data2 = cache.load(user_watches) or {}
    if setting != "none":
        data2[room1] = setting
    else:
        data2.pop(room1, None)

    if data:
        cache.save(notify_file, data, fmt="yaml")
    else:
        cache.remove(notify_file)
    if data2:
        cache.save(user_watches, data2)
    else:
        cache.remove(user_watches)


def notification_clear(user: str, room: str|None):
    """Clear one or all notifications in the user's list."""
    file = PATH_USERS_DIR / user / "notifications.txt"
    if room is None or not file.exists():
        # truncate the file to size 0
        file.write_text("")
        return
    rooms = notification_get(user)
    if room not in rooms:
        return
    rooms = [r for r in rooms if r != room]
    file.write_text("\n".join(rooms) + ("\n" if rooms else ""))


def notification_get(user: str):
    """Get a list of all notification rooms."""
    file = PATH_USERS_DIR / user / "notifications.txt"
    if not file.exists():
        return []
    return file.read_text(encoding="utf-8").splitlines()


def notification_add(user: str, room: str):
    """Add a notification if it's not already there."""
    file = PATH_USERS_DIR / user / "notifications.txt"
    rooms = notification_get(user)
    if room in rooms:
        return False
    with file.open("a", encoding="utf-8") as file:
        file.write(room + "\n")
    return True


async def notification_as_needed(user: str, room: str):
    """
    Add a notification if:
    1. user not actively viewing that room
    2. and not already there
    3. send push notification if user not active in any room
    """
    logger.info("notify: user, room:  %s  --  %s", user, room)
    user_presence_file = user_presence_file_path(user)
    if user_presence_file.exists():
        user_rooms = user_presence_file.read_text(encoding="utf-8").splitlines()
    else:
        user_rooms = []
    if room in user_rooms:
        logger.info("  already active in room")
        return

    added = notification_add(user, room)
    if not added:
        logger.info("  notification already exists")
        return
    logger.info("  added a notification")

    if not user_rooms:
        logger.info("  user not active, sending push")
        await send_push(user, room, room)


def user_presence_file_path(user: str):
    return PATH_USERS_DIR / user / "presence.txt"



def ally_notify():
    """Send a push notification to a user."""
    if len(sys.argv) != 3:
        logger.error(f"Usage: {sys.argv[0]} <user> <message>")
        sys.exit(1)

    user, message = sys.argv[1], sys.argv[2]
    asyncio.run(send_push(user, message, ""))


if __name__ == "__main__":
    ally_notify()
