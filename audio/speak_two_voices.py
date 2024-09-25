#!/usr/bin/env python3

"""
A script to speak lines with two different voices using text-to-speech.
"""

import os
import re
import logging
from functools import partial
from typing import List
import time

import sounddevice as sd
import numpy as np
import soundfile
from sh import soundstretch
from argh import arg

import speak
from ally import main, unix

__version__ = "0.1.1"

logger = main.get_logger()


def two_speakers_speak_line(males: List[str], line: str, synth, model: str) -> None:
    text = re.sub(r"[^\s]*:\s*", "", line)

    for char in males:
        if line.startswith(f"{char}:"):
            tempo, pitch = 0.8, -9
            break
    else:
        tempo, pitch = 1.2, 4

    postproc = partial(speak.postproc_soundstretch, tempo=tempo, pitch=pitch)
    speak.speak_line(
        text=text,
        model=model,
        wait=True,
        synth=synth,
        postproc=postproc,
        loud_while_speaking=100,
        echo=False,
    )


@arg("males", nargs="*", help="List of male character names")
@arg("--model", help="TTS model to use")
@arg("--silence", help="Silence duration between lines")
@arg("--start-text", help="Text to start with")
def speak_two_voices(
    *males: List[str],
    model: str = "coqui:tts_models/en/ek1/tacotron2",
    silence: float = 0.1,
    start_text: str | None = None,
) -> None:
    """Speak lines with two different voices using text-to-speech"""
    speak.add_coqui_models()
    synth = speak.get_synth(model)

    if silence > 0:
        sd.wait()
        rate = 44100
        silence_samples = int(silence * rate)
        silent_audio = np.zeros(silence_samples)
        sd.play(silent_audio, samplerate=rate)

    get, put = main.io()

    while True:
        line = get()

        if line is None:
            break
        if line == "":
            continue

        if start_text and start_text not in line:
            continue
        else:
            start_text = None
        try:
            put(line)
            with unix.redirect(stdout=None, stderr=None):
                two_speakers_speak_line(males, line, synth, model)
        except (KeyboardInterrupt, SystemExit):
            logger.warning("Interrupted, continuing with the next line in 2 seconds")
            time.sleep(2)


if __name__ == "__main__":
    main.run(speak_two_voices)
