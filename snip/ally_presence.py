#!/usr/bin/env python3-allemande

# This is unfortunately mostly included in stream.py now.

import logging
from pathlib import Path
from util import ally_path

from settings import PATH_USERS_DIR, PATH_ROOMS
from ally.cache import cache  # type: ignore # pylint: disable=wrong-import-order


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def presence_file_path(room_path: str):
    if room_path.endswith("/"):
        return room_path + ".presence"
    path = Path(room_path)
    return str(path.parent / ("." + path.name + ".presence"))


def presence_load(room: str) -> list[str]:
    """
    Load the presence file, split on newlines, return a list of users.
    """
    room_path = ally_path(room)

    presence_file = presence_file_path(room_path)
    users = (cache.load(presence_file, fmt="txt") or "").splitlines()
    return users


def presence_save(room: str, users: list[str]):
    """
    Save a list of users in the presence file.
    """
    room_path = ally_path(room)

    presence_file = presence_file_path(room_path)
    text = "\n".join(users) + ("\n" if users else "")
    cache.save(presence_file, text, fmt="txt")


def rooms_file_path(user: str):
    return str(PATH_USERS_DIR/user/"presence.txt")


def rooms_load(user: str) -> list[str]:
    """
    Load the rooms file, split on newlines, return a list of rooms.
    """
    rooms_file = rooms_file_path(user)
    rooms = (cache.load(rooms_file, fmt="txt") or "").splitlines()
    return rooms


def rooms_save(user: str, rooms: list[str]):
    """
    Save a list of rooms in the user's presence file.
    """
    rooms_file = rooms_file_path(user)
    text = "\n".join(rooms) + ("\n" if rooms else "")
    cache.save(rooms_file, text, fmt="txt")


def presence_set(user: str, room: str, present: bool):
    """
    Update the room presence file with the user's presence, also update the user's personal presence file.
    """
    users = presence_load(room)
    if user in users:
        if not present:
            users = [u for u in users if u != user]
        else:
            return
    elif present:
        users.append(user)
    else:
        return

    rooms = rooms_load(user)
    if room in rooms:
        if not present:
            rooms = [r for r in rooms if r != room]
        else:
            return
    elif present:
        rooms.append(room)
    else:
        return

    presence_save(room, users)
    rooms_save(user, rooms)
