#!/usr/bin/env python3-allemande

"""
A script to speak lines with several different voices using text-to-speech.
"""

import sys
import os
import re
import logging
from functools import partial
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


def speakers_speak_line(characters_dict: list[str, tuple], text: str, synth, model: str) -> None:
    """Speak a line with different voices"""
    character = "default"
    if m := re.match(r"^([^\s]+):\s*(.*)", text):
        character, text = m.groups()
    else:
        character = "default"

    tempo, pitch, loudness = characters_dict.get(character, characters_dict["default"])

    postproc = partial(speak.postproc_soundstretch, tempo=tempo, pitch=pitch)
    speak.speak_line(
        text=text,
        model=model,
        wait=True,
        synth=synth,
        postproc=postproc,
        loud_while_speaking=loudness,
        echo=False,
    )


@arg("characters", nargs="*", help="List of name1,name2:tempo:pitch:loud, one name can be 'default'")
@arg("--model", help="TTS model to use")
@arg("--silence", help="Silence duration between lines")
@arg("--start-text", help="Text to start with")
def speakers(
    *characters: list[str],
    model: str = "coqui:tts_models/en/ek1/tacotron2",
    silence: float = 0.1,
    start_text: str | None = None,
) -> None:
    """Speak lines with two different voices using text-to-speech"""
    get, put = main.io()

    speak.add_coqui_models()
    synth = speak.get_synth(model)

    if silence > 0:
        sd.wait()
        rate = 44100
        silence_samples = int(silence * rate)
        silent_audio = np.zeros(silence_samples)
        sd.play(silent_audio, samplerate=rate)

    characters_dict = {}

    for i in range(len(characters)):
        names, tempo, pitch, loudness = characters[i].split(":")
        tempo = float(tempo) ; pitch = float(pitch) ; loudness = int(loudness)
        for name in names.split(","):
            characters_dict[name] = (tempo, pitch, loudness)

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
#            with unix.redirect(stdout=None, stderr=None):
            speakers_speak_line(characters_dict, line, synth, model)
        except (KeyboardInterrupt, SystemExit):
            logger.warning("Interrupted, continuing with the next line in 1 second")
            time.sleep(1)


if __name__ == "__main__":
    main.run(speakers)
