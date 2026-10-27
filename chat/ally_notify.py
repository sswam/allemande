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


def send_one(subscription, message):
    """Synchronous; run via asyncio.to_thread."""
    data = json.dumps({"body": message, "room": "", "url": ""})
    webpush(
        subscription_info=subscription,
        data=data,
        vapid_private_key=VAPID_PRIVATE_KEY,
        vapid_claims={"sub": f"mailto:admin@{ALLEMANDE_DOMAIN}"},
    )


async def send_push(user, message):
    subs = load_subs(user)
    if not subs:
        logger.warning("No subscriptions found for %s.", user)
    dead = []
    for endpoint, sub in subs.items():
        try:
            # XXX we might make a lot of threads, could be better to run one thread for sending notifications to all users
            await asyncio.to_thread(send_one, sub, message)
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


def notify_set(user: str, room: str, setting: str) -> str:
    """
    Save specific notification setting in .{room}.notify or .notify for a folder.
    Lock around this if any chance of concurrency. Shouldn't be.
    """
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
    if room is None:
        # truncate the file to size 0
        file.write_text("")
        return
    lines = [l for l in file.read_text().splitlines() if l != room]
    file.write_text("\n".join(lines) + ("\n" if lines else ""))


def ally_notify():
    """Send a push notification to a user."""
    if len(sys.argv) != 3:
        logger.error(f"Usage: {sys.argv[0]} <user> <message>")
        sys.exit(1)

    user, message = sys.argv[1], sys.argv[2]
    asyncio.run(send_push(user, message))


if __name__ == "__main__":
    ally_notify()
