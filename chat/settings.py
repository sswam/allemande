#!/usr/bin/env python3-allemande

""" Allemande settings """

import os


EXTENSION = ".bb"
ROOMS_DIR = os.environ["ALLEMANDE_ROOMS"]
ALLYCHAT_CHAT_URL = os.environ["ALLYCHAT_CHAT_URL"]

ADMINS = os.environ.get("ALLYCHAT_ADMINS", "").split()
MODERATORS = os.environ.get("ALLYCHAT_MODERATORS", "").split()

ROOM_PATH_MAX_LENGTH = 1000
ROOM_MAX_DEPTH = 10
