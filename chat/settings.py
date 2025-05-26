#!/usr/bin/env python3-allemande

""" Allemande settings """

import os
from pathlib import Path


PATH_HOME   = Path(os.environ["ALLEMANDE_HOME"])
PATH_ROOMS  = Path(os.environ["ALLEMANDE_ROOMS"])
PATH_AGENTS = Path(os.environ["ALLEMANDE_AGENTS"])
PATH_VISUAL = Path(os.environ["ALLEMANDE_VISUAL"])
PATH_MODELS = Path(os.environ["ALLEMANDE_MODELS"])
PATH_WEBCACHE  = Path(os.environ["ALLEMANDE_WEBCACHE"])
# TODO put agents dir in rooms?

# TODO put some of these settings in a global reloadable config files
STARTER_PROMPT = """System:\tPlease briefly greet the user or start a conversation, in one line. You can creative, or vanilla."""

EXTENSION = ".bb"
ROOMS_DIR = os.environ["ALLEMANDE_ROOMS"]
ALLYCHAT_CHAT_URL = os.environ["ALLYCHAT_CHAT_URL"]

ADMINS = os.environ.get("ALLYCHAT_ADMINS", "").split()
MODERATORS = os.environ.get("ALLYCHAT_MODERATORS", "").split()

ROOM_PATH_MAX_LENGTH = 1000
ROOM_MAX_DEPTH = 10

LOCAL_AGENT_TIMEOUT = 10 * 60  # 10 minutes
FETCH_TIMEOUT = 30  # 30 seconds

REMOTE_AGENT_RETRIES = 3

MAX_REPLIES = 1

ADULT = os.environ.get("ALLYCHAT_ADULT", "0") == "1"
SAFE = os.environ.get("ALLYCHAT_SAFE", "1") == "1"
