#!/usr/bin/env python3-allemande

""" Allemande TTS client """

import logging
import re
from pathlib import Path
import shutil

import bb_lib
from ally import portals  # type: ignore, pylint: disable=wrong-import-order
from settings import TTS_TIMEOUT, TTS_VOICE_DEFAULT
import chat
import filters
import ally_room


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def generate_tts_file(path: Path, pathname: str):
    """ Generate a missing TTS file """
    stem = path.stem
    m = re.match(r"(\d+)\.([0-9a-f]{8})$", stem)
    if not m:
        logger.error("generate_tts_file, bad path: %r", path)
        return
    msg_id, msg_hash = m.groups()
    room_file = re.sub(r"\.tts$", r".bb", str(path.parent))

    # logger.info("pathname, room_file, msg_id, msg_hash: %r, %r, %r, %r", pathname, room_file, msg_id, msg_hash)

    messages = bb_lib.load_chat_messages(room_file)

    try:
        message = messages[int(msg_id)]
    except IndexError:
        logger.error("generate_tts_file, chat file too short or missing: %s >= %s", msg_id, len(messages))
        return

    user = message.user
    content = message.content

    check_hash = bb_lib.message_hash({"user":user, "content":content})
    if check_hash != msg_hash:
        logger.error("generate_tts_file, hash mismatch: %s vs %s", msg_hash, check_hash)
        # user needs to reload the page, or HTML is out of sync with bb file
        return

    # TODO select a voice for the user / agent somehow...!  oh oh...  maybe can cache those settings in room options even for the default?

    # clean up stuff we likely don't want to speak!
    content, _n_own_messages = chat.remove_thinking_sections(content, None, 0)
    content = filters.filter_in_remove_code(content, 0)
    content = filters.filter_in_remove_images(content, 0)
    content = re.sub(r"\*.*?\*", "", content)

    # handle empty content
    if not content:
        path.write_text("")
        return

    agents_dict = ally_room.read_agents_dicts(Path(room_file).parent)
    voice = agents_dict.get(user.lower(), {}).get("voice", TTS_VOICE_DEFAULT)

    logger.info("generate_tts_file: %s %s %s", room_file, msg_id, voice)

    # XXX TODO access control - here or perhaps in core/tts_omnivoice
    # XXX TODO locking

    config = { "voice": voice }

    service = "tts_omnivoice"
    portal = portals.get_portal(service)

    response, resp = await client_request(portal, content, config=config, timeout=TTS_TIMEOUT)

    try:
        path.parent.mkdir(exist_ok=True)
        shutil.copy(response, path)
    except Exception as e:
        logger.error("generate_tts_file, response / copy failed: %r", e)

    await portal.remove_response(resp)


async def client_request(portal, input_text, config=None, timeout=None):
    """Call the core server and get a response."""

    req = await portal.prepare_request(config)

    req_input = req / "request.txt"
    req_input.write_text(input_text, encoding="utf-8")

    await portal.send_request(req)

    resp, status = await portal.wait_for_response(req, timeout=timeout)

    if status == "error":
        await portal.response_error(resp)  # raises RuntimeError?!

    response = resp / "response.mp3"

    return response, resp
