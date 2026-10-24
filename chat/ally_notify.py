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


def subs_path(user_id):
    return PATH_USERS_DIR / user_id / "push_subscriptions.json"


def load_subs(user_id):
    try:
        with open(subs_path(user_id), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_subs(user_id, subs):
    with open(subs_path(user_id), "w", encoding="utf-8") as f:
        json.dump(subs, f, indent=2)


def subscribe(user_id, sub):
    subs = load_subs(user_id)
    subs[sub["endpoint"]] = sub
    save_subs(user_id, subs)


def unsubscribe(user_id, endpoint):
    subs = load_subs(user_id)
    subs.pop(endpoint, None)
    save_subs(user_id, subs)


def send_one(subscription, message):
    """Synchronous; run via asyncio.to_thread."""
    data = json.dumps({"body": message, "room": "", "url": ""})
    webpush(
        subscription_info=subscription,
        data=data,
        vapid_private_key=VAPID_PRIVATE_KEY,
        vapid_claims={"sub": f"mailto:admin@{ALLEMANDE_DOMAIN}"},
    )


async def send_push(user_id, message):
    subs = load_subs(user_id)
    if not subs:
        logger.warning("No subscriptions found for %s.", user_id)
    dead = []
    for endpoint, sub in subs.items():
        try:
            # XXX we might make a lot of threads, could be better to run one thread for sending notifications to all users
            await asyncio.to_thread(send_one, sub, message)
        except WebPushException as e:
            logger.error("Push failed for %s: %s", user_id, e)
            if e.response is not None and e.response.status_code in (404, 410):
                dead.append(endpoint)
    if dead:
        for ep in dead:
            del subs[ep]
        save_subs(user_id, subs)
        logger.warning("Removed %s dead subscription(s).", len(dead))


def notify_file_path(room_path):
    if room_path.endswith("/"):
        return room_path + ".notify"
    path = Path(room_path)
    return str(path.parent / ("." + path.name + ".notify"))


def notify_get(user_id: str, room: str) -> tuple[str | None, str | None]:
    """
    Check .{room}.notify, .notify and parent .notify files
    Returns:
    (specific, inherited): The setting for this specific room (may be None),
        and the inherited setting from a parent (may be None)
    """
    room_path = ally_path(room)
    specific = None
    inherited = None

    # Check the specific room first
    notify_file = notify_file_path(room_path)
    data = cache.load(notify_file, fmt="yaml") or {}
    specific = data.get(user_id)

    # Walk up the parent directories for inherited setting
    while True:
        room_path = str(Path(room_path).parent) + "/"
        if not room_path.startswith(str(PATH_ROOMS)):
            break
        notify_file = notify_file_path(room_path)
        data = cache.load(notify_file, fmt="yaml") or {}
        inherited = data.get(user_id)
        if inherited is not None:
            break

    return specific, inherited


def notify_set(user_id: str, room: str, setting: str|None) -> str:
    """
    Save specific notification setting in .{room}.notify or .notify for a folder.
    Lock around this if any chance of concurrency. Shouldn't be.
    """
    room_path = ally_path(room)
    notify_file = notify_file_path(room_path)

    data = cache.load(notify_file, fmt="yaml") or {}
    if setting is not None:
        data[user_id] = setting
    else:
        data.pop(user_id, None)

    # Also save in users list of all watches, by room

    user_watches = PATH_USERS_DIR / user_id / "notify.json"
    l = len(str(PATH_ROOMS)) + 1
    room1 = room_path[l:]

    data2 = cache.load(user_watches) or {}
    if setting is not None:
        data2[room1] = setting
    else:
        data2.pop(room1, None)

    cache.save(notify_file, data, fmt="yaml")
    cache.save(user_watches, data2)


def ally_notify():
    """Send a push notification to a user."""
    if len(sys.argv) != 3:
        logger.error(f"Usage: {sys.argv[0]} <user_id> <message>")
        sys.exit(1)

    user_id, message = sys.argv[1], sys.argv[2]
    asyncio.run(send_push(user_id, message))


if __name__ == "__main__":
    ally_notify()
