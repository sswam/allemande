#!/usr/bin/env python3-allemande

"""
This module provides text-to-speech functionality with various TTS engines and models.
"""

import os
import sys
import tempfile
import time
from functools import partial
from typing import TextIO

import alsaaudio  # type: ignore
import numpy as np
import sounddevice as sd  # type: ignore
import soundfile  # type: ignore
import torch
from gtts import gTTS  # type: ignore
from sh import amixer, soundstretch  # type: ignore
from TTS.api import TTS  # type: ignore
from TTS.utils.manage import ModelManager  # type: ignore
from TTS.utils.synthesizer import Synthesizer  # type: ignore

from ally import main, logs  # type: ignore

__version__ = "0.1.4"

logger = logs.get_logger()

DEFAULT_MODELS = {
    "coqui": "tts_models/en/ek1/tacotron2",
    "gtts": "en:co.uk",
}

# DEFAULT_MODEL = "coqui:" + DEFAULT_MODELS['coqui']
DEFAULT_MODEL = "gtts:" + DEFAULT_MODELS["gtts"]

use_cuda = torch.cuda.is_available()


def get_synth_coqui(model=DEFAULT_MODELS["coqui"]):
    """Get a Coqui TTS speak function for the given model"""
    global use_cuda

    # download and load the TTS model
    model_manager = ModelManager()
    model_path, config_path, _model_item = model_manager.download_model(model)

    # create a TTS synthesizer
    synth = Synthesizer(
        tts_checkpoint=model_path,
        tts_config_path=config_path,
        vocoder_checkpoint=None,
        use_cuda=use_cuda,
    )

    def speak_fn(text, out, **_kwargs):
        audio = synth.tts(text)
        stem, ext = os.path.splitext(out)
        if ext != ".wav":
            out = stem + ".wav"
        synth.save_wav(audio, out)
        rate = synth.tts_config.audio["sample_rate"]
        return out, audio, rate

    return speak_fn


def get_synth_gtts(model=DEFAULT_MODELS["gtts"]):
    """Get a Google TTS speak function for the given model"""
    lang, *rest = model.split(":", 1)
    tld = rest[0] if rest else None
    kwargs = {"lang": lang}
    if tld:
        kwargs["tld"] = tld

    def speak_fn(text, out, **_kwargs):
        tts = gTTS(text=text, **kwargs)
        stem, ext = os.path.splitext(out)
        outmp3 = out
        if ext != ".mp3":
            outmp3 = stem + ".mp3"
        tts.save(outmp3)
        audio, rate = soundfile.read(outmp3)
        if ext == ".wav":
            soundfile.write(out, audio, rate, subtype="PCM_16")
        else:
            out = outmp3
        return out, audio, rate

    return speak_fn


engines = {
    "coqui": get_synth_coqui,
    "gtts": get_synth_gtts,
}

gtts_models = [
    {"id": "en:com.au", "accent": "English (Australia)"},
    {"id": "en:co.uk", "accent": "English (United Kingdom)"},
    {"id": "en:us", "accent": "English (United States)"},
    {"id": "en:ca", "accent": "English (Canada)"},
    {"id": "en:co.in", "accent": "English (India)"},
    {"id": "en:ie", "accent": "English (Ireland)"},
    {"id": "en:co.za", "accent": "English (South Africa)"},
    {"id": "fr:ca", "accent": "French (Canada)"},
    {"id": "fr:fr", "accent": "French (France)"},
    {"id": "zh-CN:any", "accent": "Mandarin (China Mainland)"},
    {"id": "zh-TW:any", "accent": "Mandarin (Taiwan)"},
    {"id": "pt:com.br", "accent": "Portuguese (Brazil)"},
    {"id": "pt:pt", "accent": "Portuguese (Portugal)"},
    {"id": "es:com.mx", "accent": "Spanish (Mexico)"},
    {"id": "es:es", "accent": "Spanish (Spain)"},
    {"id": "es:us", "accent": "Spanish (United States)"},
]

models = {}


def add_coqui_models():
    """Add Coqui TTS models to the models dict"""
    for mid in TTS().list_models():
        full_id = "coqui:" + mid
        lang = mid.split("/")[1]
        models[full_id] = {
            "engine": "coqui",
            "id": mid,
            "lang": lang,
        }


def add_gtts_models():
    """Add Google TTS models to the models dict"""
    for model in gtts_models:
        mid = model["id"]
        full_id = "gtts:" + mid
        lang, tld = mid.split(":")
        models[full_id] = {
            "engine": "gtts",
            "id": mid,
            "lang": lang,
            "tld": tld,
            "accent": model["accent"],
        }


def download_all_coqui_models():
    """Download all Coqui TTS models"""
    for model_name in TTS.list_models():
        _tts = TTS(model_name)


# TODO coqui speaker selection


def get_synth(model=DEFAULT_MODEL):
    """Get a TTS speak function for the given model"""
    model_type, *rest = model.split(":", 1)
    model = rest[0] if rest else DEFAULT_MODELS[model_type]
    try:
        engine = engines[model_type]
    except KeyError as e:
        raise ValueError(f"Unknown engine: {model_type}") from e
    return engine(model)


class SpeakContext:
    """Context manager for handling microphone and volume state during speech."""
    def __init__(self, deafen=False, loud_while_speaking=None):
        self.deafen = deafen
        self.loud_while_speaking = loud_while_speaking
        self.vol = None

    def __enter__(self):
        if self.deafen:
            sd.wait()
            amixer.sset("Capture", "nocap")
            logger.debug("Mic off")
        if self.loud_while_speaking is not None:
            self.vol = alsaaudio.Mixer().getvolume()[0]
            alsaaudio.Mixer().setvolume(self.loud_while_speaking)
            logger.info("speak_line: volume %r -> %r", self.vol, self.loud_while_speaking)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.deafen:
            sd.wait()
            amixer.sset("Capture", "cap")
            logger.debug("Mic on")
        if self.loud_while_speaking:
            alsaaudio.Mixer().setvolume(self.vol)
            logger.info("speak_line: volume %r <- %r", self.vol, self.loud_while_speaking)


def speak_line(
    text,
    out=None,
    model=DEFAULT_MODEL,
    play=True,
    wait=True,
    synth=None,
    deafen=False,
    postproc=None,
    echo=True,
    loud_while_speaking=None,
):
    """Speak a line of text"""

    logger.info(
        "speak_line: text: %r, out: %r, model: %r, play: %r, wait: %r, synth: %r, deafen: %r, postproc: %r, echo: %r, loud_while_speaking: %r",
        text,
        out,
        model,
        play,
        wait,
        synth,
        deafen,
        postproc,
        echo,
        loud_while_speaking,
    )

    if not synth:
        synth = get_synth(model)

    logger.info("speak_line: text: %r", text)
    if echo:
        print(text)

    # 	if line.strip() == "":
    # 		# sleep a bit
    # 		time.sleep(0.5)
    # 		return

    with SpeakContext(deafen=deafen, loud_while_speaking=loud_while_speaking):
        # create a temporary file to store the audio output
        out_is_temp = not out
        if out_is_temp:
            with tempfile.NamedTemporaryFile(prefix="speak_", suffix=".wav", delete=False) as f:
                out = f.name
        try:
            # generate speech from the input text
            file, audio, rate = synth(text, out=out)

            rate_pp = rate
            if postproc:
                audio, rate_pp = postproc(file, audio, rate)

            if deafen:
                sd.wait()
                amixer.sset("Capture", "nocap")
                logger.debug("Mic off")

            # play the audio
            if play:
                sd.wait()

                sd.play(audio, samplerate=rate_pp)

        except AssertionError as e:
            if "No text" in str(e):
                time.sleep(0.5)
            else:
                raise e
        except ZeroDivisionError as e:
            logger.error("speak_line: ignoring ZeroDivisionError: %r", e)
        finally:
            if deafen:
                sd.wait()
                amixer.sset("Capture", "cap")
                logger.debug("Mic on")
            if out_is_temp:
                os.remove(out)

        if play and wait:
            sd.wait()


def speak_lines(
    istream=sys.stdin,
    out=None,
    model=DEFAULT_MODEL,
    play=True,
    wait=True,
    synth=None,
    deafen=False,
    postproc=None,
    echo=True,
    loud_while_speaking=None,
):
    """Speak lines of text"""
    if not synth:
        synth = get_synth(model)
    if out:
        stem, ext = os.path.splitext(out)

    logger.info("ready to speak lines")

    for i, line in enumerate(istream):
        logger.debug("speak_lines: line: %r", line)
        if out:
            out = f"{stem}_{i:06d}{ext}"
        speak_line(
            text=line,
            out=out,
            model=model,
            play=play,
            wait=wait,
            synth=synth,
            deafen=deafen,
            postproc=postproc,
            echo=echo,
            loud_while_speaking=loud_while_speaking,
        )

    if play and wait:
        sd.wait()


def postproc_soundstretch(file, audio, rate, tempo=1, pitch=0):
    """Post-process audio with soundstretch"""

    # TODO use a python module instead of shelling out?
    # - soundstretch module is not based on libsoundtouch
    # - pysoundtouch is based on libsoundtouch but it's not in pypi, maybe not maintained?
    stem, ext = os.path.splitext(file)

    if ext != ".wav":
        file = stem + ".wav"
        soundfile.write(file, audio, rate, subtype="PCM_16")

    with tempfile.NamedTemporaryFile(prefix="speak_", suffix="_pp.wav") as pp:
        pp_out = pp.name
        tempo_percent = round((tempo - 1) * 100)
        soundstretch(file, pp_out, f"-tempo={tempo_percent}", f"-pitch={pitch}", "-speech")
        audio, rate = soundfile.read(pp_out)

    if ext != ".wav":
        os.remove(file)

    # load the audio data from the wav file
    return audio, rate


def do_list_models():
    """List available models"""
    for k, v in models.items():
        _mid = v["id"]
        lang = v["lang"]
        tld = v.get("tld", "")
        accent = v.get("accent", "")
        print("\t".join([k, lang, tld, accent]))


def speak(
    istream: TextIO = sys.stdin,
    out: str | None = None,
    text: str | None = None,
    model: str = DEFAULT_MODEL,
    silence: float = 0.1,
    play: bool = True,
    wait: bool = True,
    deafen: bool = False,
    tempo: float = 1.0,
    pitch: float = 0.0,
    list_models: bool = False,
    cuda: bool = False,
    download_all_models: bool = False,
    echo: bool = True,
    loud_while_speaking: int = 100,
) -> None:
    """Speak text using the specified TTS model and options."""
    global use_cuda

    if not cuda:
        use_cuda = False

    if download_all_models:
        download_all_coqui_models()
        sys.exit(0)

    add_gtts_models()
    add_coqui_models()
    if list_models:
        do_list_models()
        sys.exit(0)

    synth = get_synth(model)

    # TODO put various options into a dict or something so we can pass them around more easily

    # Play an optional short silence to wake up the speakers
    if silence > 0 and play:
        sd.wait()
        rate = 44100
        silence_samples = int(silence * rate)
        silent_audio = np.zeros(silence_samples)
        sd.play(silent_audio, samplerate=rate)

    postproc = None
    if tempo != 1 or pitch != 0:
        postproc = partial(postproc_soundstretch, tempo=tempo, pitch=pitch)

    if text:
        logger.info("speak: text: %r", text)
        speak_line(
            text=text,
            out=out,
            model=model,
            play=play,
            wait=wait,
            synth=synth,
            deafen=deafen,
            postproc=postproc,
            echo=echo,
            loud_while_speaking=loud_while_speaking,
        )
    else:
        logger.info("speak: reading from stdin")
        speak_lines(
            istream=istream,
            out=out,
            model=model,
            play=play,
            wait=wait,
            synth=synth,
            deafen=deafen,
            postproc=postproc,
            echo=echo,
            loud_while_speaking=loud_while_speaking,
        )


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("--model", "-m", help="TTS model to use")
    arg("--silence", type=float, help="Duration of initial silence")
    arg("--no-play", dest="play", action="store_false", help="Don't play audio")
    arg("--no-wait", dest="wait", action="store_false", help="Don't wait for audio to finish")
    arg("--deafen", action="store_true", help="Mute microphone while speaking")
    arg("--tempo", type=float, help="Adjust speaking tempo")
    arg("--pitch", type=float, help="Adjust pitch")
    arg("--list-models", action="store_true", help="List available models")
    arg("--cuda", action="store_true", help="Use CUDA if available")
    arg("--download-all-models", action="store_true", help="Download all Coqui TTS models")
    arg("--no-echo", dest="echo", action="store_false", help="Don't echo text to stdout")
    arg("--loud-while-speaking", type=int, help="Volume level while speaking")
    arg("text", nargs="?", help="Text to speak")


if __name__ == "__main__":
    main.go(speak, setup_args)
    sd.wait()


# TODO:

# - check out https://github.com/nateshmbhat/pyttsx3
# - try other Coqui TTS models and options
# - maybe use an OO approach
# - maybe port to Mac, Windows (mixer stuff)


# alt idea for controlling the Linux mixer:
#
# import alsaaudio
#
# def deafen(device_name='Capture'):
# 	mixer = alsaaudio.Mixer(device_name)
# 	mixer.setrec(0)
#
# def undeafen(device_name='Capture'):
# 	mixer = alsaaudio.Mixer(device_name)
# 	mixer.setrec(1)
#
# if __name__ == '__main__':
# 	deafen()
# 	time.sleep(5)  # Example: Sleep for 5 seconds while the microphone is muted
# 	undeafen()

# Ideally, it would be better just to tell the mike app not to record during this time.
