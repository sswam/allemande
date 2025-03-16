#!/usr/bin/env python3-allemande
""" Transcribe speech to text using microphone input and whisper """

import sys
import signal
import atexit
import io
from threading import Thread, Event
from queue import Queue
import logging
from contextlib import contextmanager
from pathlib import Path
import asyncio

import alsaaudio  # pylint: disable=no-name-in-module
from pydub import AudioSegment
import speech_recognition as sr
import yaml

import ucm
from ally import portals, main, logs

__version__ = "0.1.1"

logger = logs.get_logger()

default_service = "stt_whisper"

TIMEOUT = 1 * 60  # 1 minute


@contextmanager
def open_microphone_spamfree(*args, **kwargs):
    """Open microphone without spamming stderr"""
    try:
        with ucm.redirect_stderr_to_dev_null():
            source = sr.Microphone(*args, **kwargs).__enter__()  # pylint: disable=unnecessary-dunder-call
        yield source
    finally:
        source.__exit__(None, None, None)


def record_speech(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    run_event, q_audio, energy, pause, non_speaking_duration, dynamic_energy, device_index, adjust_for_ambient_noise=False
):
    """Record audio from microphone and put it in the queue"""
    r = sr.Recognizer()
    r.energy_threshold = energy
    r.pause_threshold = pause
    r.non_speaking_duration = non_speaking_duration
    r.dynamic_energy_threshold = dynamic_energy
    i = 0

    if logger.getEffectiveLevel() <= logging.DEBUG:
        open_microphone = sr.Microphone
    else:
        open_microphone = open_microphone_spamfree

    first = True

    with open_microphone(sample_rate=16000, device_index=device_index) as source:
        while run_event.is_set():
            if adjust_for_ambient_noise:
                logger.debug("Adjusting for ambient noise")
                r.adjust_for_ambient_noise(source)

            if first:
                logger.info("Listening")
                first = False
            else:
                logger.debug("Listening")
            audio = r.listen(source)
            logger.debug("Got audio")

            q_audio.put_nowait(audio)
            i += 1
    q_audio.put_nowait(None)


async def client_request(portal, audio, config=None):
    """Call the core server and get a response."""
    req = await portal.prepare_request(config=config)
    req_audio = req / "request.aud"

    data = io.BytesIO(audio.get_wav_data())
    audio_clip = AudioSegment.from_file(data)
    audio_clip.export(str(req_audio), format="flac")

    await portal.send_request(req)
    status = "error"
    try:
        resp, status = await portal.wait_for_response(req, timeout=TIMEOUT)
    except TimeoutError as e:
        logger.error("Timeout waiting for response: %s", e)
    if status == "error":
        await portal.response_error(resp)

    text = (resp / "text.txt").read_text(encoding="utf-8")
#    result = yaml.safe_load((resp / "result.yaml").read_text(encoding="utf-8"))

#    logger.info("%r", result)
    await portal.remove_response(resp)

    return text #, result


async def speech_to_text_async(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    portal, run_event, q_audio, q_text, lang, confidence_threshold=0.8
):
    """Transcribe from the audio queue to the text queue"""
    config = {
        "language": lang,
    }

    while run_event.is_set():
        audio = q_audio.get()
        if audio is None:
            break

        text = await client_request(portal, audio, config=config)
#        text, result = await client_request(portal, audio, config=config)

        text = text.strip()
        if text:
            q_text.put_nowait(text)
#         segs = result["segments"]
#         no_speech_prob = sum(x["no_speech_prob"] for x in segs) / (len(segs) or 1)
#         if text and no_speech_prob < (1 - confidence_threshold):
#             q_text.put_nowait(text)

    q_text.put_nowait(None)


def speech_to_text(portal, run_event, q_audio, q_text, lang, confidence_threshold=0.8):
    """Transcribe from the audio queue to the text queue"""
    asyncio.run(speech_to_text_async(portal, run_event, q_audio, q_text, lang, confidence_threshold))


def do_list_devices():
    """List available microphone devices"""
    for index, name in enumerate(sr.Microphone.list_microphone_names()):
        print(f"{index}\t{name}")


def mike(  # pylint: disable=too-many-arguments,too-many-locals,too-many-positional-arguments
    lang: str = "en",
    energy: int = 150,
    dynamic_energy: bool = False,
    pause: float = 1.0,
    non_speaking_duration: float = 1.0,
    device_index: int | None = None,
    list_devices: bool = False,
    adjust_for_ambient_noise: bool = False,
    service: str = default_service,
    confidence_threshold: float = 0.6,
    quiet_while_listening: int | None = 40,
):
    """Transcribe speech to text using microphone input"""
    if list_devices:
        do_list_devices()
        sys.exit(0)

    if quiet_while_listening is not None:
        vol = alsaaudio.Mixer().getvolume()[0]  # pylint: disable=c-extension-no-member
        alsaaudio.Mixer().setvolume(quiet_while_listening)  # pylint: disable=c-extension-no-member

        def reset_volume(*args, exit=True):  # pylint: disable=redefined-builtin,unused-argument
            alsaaudio.Mixer().setvolume(vol)  # pylint: disable=c-extension-no-member
            if exit:
                sys.exit(0)

        signal.signal(signal.SIGINT, reset_volume)
        signal.signal(signal.SIGTERM, reset_volume)
        atexit.register(reset_volume, exit=False)

    portal = portals.get_portal(service)
    run_event = Event()
    run_event.set()

    try:
        q_audio = Queue()
        q_text = Queue()
        Thread(
            target=record_speech,
            args=(run_event, q_audio, energy, pause, non_speaking_duration, dynamic_energy, device_index, adjust_for_ambient_noise),
        ).start()
        Thread(target=speech_to_text, args=(portal, run_event, q_audio, q_text, lang, confidence_threshold)).start()

        while True:
            text = q_text.get()
            if text is None:
                break
            print(text)
            sys.stdout.flush()
    except KeyboardInterrupt:
        logger.exception("Interrupted!")
    finally:
        run_event.clear()


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("--lang", "-l", help="Language")
    arg("--energy", "-e", help="Energy threshold")
    arg("--dynamic-energy", "-E", help="Dynamic energy threshold")
    arg("--pause", "-p", help="Pause threshold")
    arg("--non-speaking-duration", "-n", help="Non-speaking duration")
    arg("--device-index", "-i", help="Device index")
    arg("--list-devices", "-L", help="List devices")
    arg("--adjust-for-ambient-noise", "-a", help="Adjust for ambient noise")
    arg("--service", "-s", help="Portal service for speech to text")
    arg("--confidence-threshold", "-c", help="Confidence threshold")
    arg("--quiet-while-listening", "-m", help="Quiet or mute speakers while listening, volume level")


if __name__ == "__main__":
    main.go(mike, setup_args)
