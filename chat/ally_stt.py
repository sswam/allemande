#!/usr/bin/env python3-allemande

""" Allemande speech to text client """

import logging
import re
from pathlib import Path
import shutil

# from tinytag import TinyTag
# from mutagen.matroska import Matroska

import bb_lib
from ally import portals  # type: ignore, pylint: disable=wrong-import-order
from settings import STT_TIMEOUT, STT_MAX_LENGTH
import chat
import filters
import ally_room


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def convert_audio_to_text(path: Path):
    """ Transcribe audio to text """

    # # TODO check if audio file is too long, maybe 5m limit
    # # but tinytag and mutagen do not support webm!
    # if path.suffix == ".webm":
    #     audio = Matroska(path)
    #     duration = audio.info.length
    # else:
    #     tag = TinyTag.get(path)
    #     duration = tag.duration
    # if tag.duration > STT_MAX_LENGTH:
    #     raise ValueError(f"audio file too long for STT: {tag.duration:.2f}")

    config = {}  # language, model

    service = "stt_whisper"
    portal = portals.get_portal(service)

    text, resp = await client_request(portal, path, config=config, timeout=STT_TIMEOUT)

    await portal.remove_response(resp)

    return text


async def client_request(portal, audio_path, config=None, timeout=None):
    """Call the core server and get a response."""

    req = await portal.prepare_request(config)

    req_input = req / "request.aud"
    shutil.copy(audio_path, req_input)

    await portal.send_request(req)

    resp, status = await portal.wait_for_response(req, timeout=timeout)

    if status == "error":
        await portal.response_error(resp)  # raises RuntimeError?!

    response = resp / "text.txt"

    text = response.read_text(encoding="utf-8")

    return text, resp
