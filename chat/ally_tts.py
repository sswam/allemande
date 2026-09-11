#!/usr/bin/env python3-allemande

""" Allemande text to speech client """

import logging
import re
from pathlib import Path
import shutil
import asyncio

import bb_lib
from ally import portals  # type: ignore, pylint: disable=wrong-import-order
from settings import TTS_TIMEOUT, TTS_VOICE_DEFAULT, TTS_VOICE_HUMAN_DEFAULT, TTS_VOICE_NARRATION
import chat
import filters
import ally_room


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


_tts_locks = {}


def get_tts_lock(key):
    """ Get a lock to prevent concurrent TTS generation of the same file """
    if key not in _tts_locks:
        _tts_locks[key] = asyncio.Lock()
    return _tts_locks[key]


async def generate_tts_file(path: Path, regen=False):
    """ Generate a TTS file if needed, with locking """
    lock = get_tts_lock(str(path))
    async with lock:
        if regen or not path.exists():
            await generate_tts_file_2(path)


async def generate_tts_file_2(path: Path):
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

    # clean up stuff we likely don't want to speak!
    content, _n_own_messages = chat.remove_thinking_sections(content, None, 0)
    content = filters.filter_in_remove_code(content, 0)
    content = filters.filter_in_remove_images(content, 0)
    content = re.sub(r"(^|\s)@(\w)", r"\2", content)  # strip @ signs from @mentions
    content = re.sub(r"<script\b.*?>.*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE)  # strip out script containers
    content = re.sub(r"<style\b.*?>.*?</style>", "", content, flags=re.DOTALL | re.IGNORECASE)  # strip out style containers
    content = re.sub(r"<!--.*?-->", "", content, flags=re.DOTALL)  # strip out HTML comments
    content = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", content)  # replace links with just the link text
    content = re.sub(r"<[A-Za-z/].*?>", "", content)  # strip out HTML tags
    # content = re.sub(r"\*.*?\*", "", content)  # remove *italics / actions* - disabled for now as it's flaky

    # experimental:  add a fullstop at the end of each line if it ends with a word character
    content = re.sub(r"(\w|\*)$", r"\1.", content, flags=re.MULTILINE)

    logger.info("cleaned up content for TTS: %s", content)

    path.parent.mkdir(exist_ok=True)

    # handle empty content
    if not content:
        path.write_text("")
        return

    agents_dict = ally_room.read_agents_dicts(Path(room_file).parent, include_human=True)
    agent = user and agents_dict.get(user.lower())
    if user is None:
        voice = TTS_VOICE_NARRATION
    elif agent is not None and agent.get("type") != "human":
        voice = agent.get("voice", TTS_VOICE_DEFAULT)
    elif agent is not None:
        voice = agent.get("voice", TTS_VOICE_HUMAN_DEFAULT)
    else:
        voice = TTS_VOICE_HUMAN_DEFAULT

    logger.info("generate_tts_file: %s %s %s", room_file, msg_id, voice)

    # XXX TODO access control - here or perhaps in core/tts_omnivoice
    # XXX TODO locking

    config = { "voice": voice }

    service = "tts_omnivoice"
    portal = portals.get_portal(service)

    response, resp = await client_request(portal, content, config=config, timeout=TTS_TIMEOUT)

    try:
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
