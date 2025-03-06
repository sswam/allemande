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
from TTS.api import TTS  # type: ignore
from TTS.utils.manage import ModelManager  # type: ignore
from TTS.utils.synthesizer import Synthesizer  # type: ignore
from parler_tts import ParlerTTSForConditionalGeneration  # type: ignore
from transformers import AutoTokenizer  # type: ignore
from pydantic import BaseModel, ConfigDict
import spacy
from sh import amixer, soundstretch  # type: ignore # pylint: disable=no-name-in-module

from ally import main, logs, geput  # type: ignore

__version__ = "0.1.6"

os.environ["TOKENIZERS_PARALLELISM"] = "false"


logger = logs.get_logger()

DEFAULT_MODELS = {
    "coqui": "tts_models/en/ek1/tacotron2",
    "gtts": "en:co.uk",
    "parler": "mini-v1",
}

# DEFAULT_MODEL = "coqui:" + DEFAULT_MODELS['coqui']
# DEFAULT_MODEL = "gtts:" + DEFAULT_MODELS["gtts"]
DEFAULT_MODEL = "parler:" + DEFAULT_MODELS["parler"]

DEFAULT_PARLER_PROMPT = "Laura, very clear audio."


def parler_compile(parler, description_tokenizer, opts, device):
    """Compile the Parler TTS model for speed"""
    torch.set_float32_matmul_precision('high')  # XXX?

    logger.info("Compiling model with mode: %s", opts.compile)
    # Set cache implementation for compilation
    parler.generation_config.cache_implementation = "static"
    parler.forward = torch.compile(parler.forward, mode=opts.compile)

    # Warmup compilation with dummy input
    max_length = 50
    dummy_text = "This is for compilation"
    inputs = description_tokenizer(dummy_text, return_tensors="pt",
                                padding="max_length", max_length=max_length).to(device)
    model_kwargs = {
        **inputs,
        "prompt_input_ids": inputs.input_ids,
        "prompt_attention_mask": inputs.attention_mask,
    }

    n_steps = 2 if opts.compile == "reduce_overhead" else 1
    for _ in range(n_steps):
        _ = parler.generate(**model_kwargs)


def get_synth_parler(model: str = DEFAULT_MODELS["parler"], opts=None):
    """Get a Parler TTS speak function for the given model variant"""
    info = models[f"parler:{model}"]
    model_name = f"parler-tts/parler-tts-{model}"
    sdk = info.get("sdk", "1")
    device = "cpu" if opts.cpu else "cuda:0"
#    torch_dtype = torch.bfloat16

    parler = ParlerTTSForConditionalGeneration.from_pretrained(model_name).to(device)
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if sdk == "1":
        logger.info("Using same tokenizer")
        description_tokenizer = tokenizer
    else:
        tokenizer_name = parler.config.text_encoder._name_or_path  # pylint: disable=protected-access
        logger.info("Using separate tokenizer: %s", tokenizer_name)
        description_tokenizer = AutoTokenizer.from_pretrained(tokenizer_name)

    # Compile if requested
    if hasattr(opts, "compile") and opts.compile and opts.compile != "none":
        parler_compile(parler, description_tokenizer, opts, device)

    def speak_fn(text, out, prompt=opts.prompt, **_kwargs):
        if prompt is None:
            prompt = DEFAULT_PARLER_PROMPT

        # This is a bit confusing, as I call the 'description' the prompt,
        # but they call the input 'text' the prompt:
        input_ids = description_tokenizer(prompt, return_tensors="pt").input_ids.to(device)
        prompt_input_ids = tokenizer(text, return_tensors="pt").input_ids.to(device)

        generation = parler.generate(input_ids=input_ids, prompt_input_ids=prompt_input_ids)
        audio = generation.cpu().numpy().squeeze()
        rate = parler.config.sampling_rate

        if out:
            soundfile.write(out, audio, rate)
        return out, audio, rate

    return speak_fn


def get_synth_coqui(model=DEFAULT_MODELS["coqui"], opts=None):
    """Get a Coqui TTS speak function for the given model"""
    # download and load the TTS model
    model_manager = ModelManager()
    model_path, config_path, _model_item = model_manager.download_model(model)

    # create a TTS synthesizer
    synth = Synthesizer(
        tts_checkpoint=model_path,
        tts_config_path=config_path,
        vocoder_checkpoint=None,
        use_cuda=not opts.cpu,
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


def get_synth_gtts(model=DEFAULT_MODELS["gtts"], opts=None):  # pylint: disable=unused-argument
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
            os.remove(outmp3)
        else:
            out = outmp3
        return out, audio, rate

    return speak_fn


engines = {
    "coqui": get_synth_coqui,
    "gtts": get_synth_gtts,
    "parler": get_synth_parler,
}

parler_models = [
    {"id": "mini-v1", "lang": "en", "sdk": "1"},
    {"id": "large-v1", "lang": "en", "sdk": "1"},
    {"id": "mini-v1.1", "lang": "en", "sdk": "1.1"},
    {"id": "mini-multilingual", "lang": "en,fr,es,pt,pl,de,it,nl", "sdk": "1.1"},
    {"id": "mini-expresso", "lang": "en", "sdk": "1"},
]

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


def add_parler_models():
    """Add Parlert TTS models to the models dict"""
    for model in parler_models:
        mid = model["id"]
        full_id = "parler:" + mid
        models[full_id] = {
            "engine": "parler",
            "id": mid,
            "lang": model["lang"],
        }


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


def get_synth(model=DEFAULT_MODEL, opts=None):
    """Get a TTS speak function for the given model"""
    model_type, *rest = model.split(":", 1)
    model = rest[0] if rest else DEFAULT_MODELS[model_type]
    try:
        engine = engines[model_type]
    except KeyError as e:
        raise ValueError(f"Unknown engine: {model_type}") from e
    return engine(model, opts)


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
            self.vol = alsaaudio.Mixer().getvolume()[0]  # pylint: disable=c-extension-no-member
            alsaaudio.Mixer().setvolume(self.loud_while_speaking)  # pylint: disable=c-extension-no-member
            logger.info("speak_line: volume %r -> %r", self.vol, self.loud_while_speaking)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self.deafen:
            sd.wait()
            amixer.sset("Capture", "cap")
            logger.debug("Mic on")
        if self.loud_while_speaking:
            alsaaudio.Mixer().setvolume(self.vol)  # pylint: disable=c-extension-no-member
            logger.info("speak_line: volume %r <- %r", self.vol, self.loud_while_speaking)


def speak_line(out=None, text=None, synth=None, postproc=None, opts=None):  # pylint: disable=too-many-branches, too-many-statements
    """Speak a line of text"""

    if opts.read_prompts and "\t" in text:
        prompt_2, text = text.split("\t", 1)
    elif opts.read_prompts and text.strip() != "":
        prompt_2 = "-"
        logger.debug("speak_line: no tab in text: %r", text)
    else:
        prompt_2 = ""

    if opts.read_prompts_add and prompt_2:
        prompt = opts.prompt + " " + prompt_2
    elif opts.read_prompts_add:
        prompt = opts.prompt
    elif prompt_2 == "-":
        prompt = opts.prompt
    else:
        prompt = prompt_2

    # split the text into sentences
    if opts.split_sentences:
        sentences = [sent.text.strip() for sent in opts.nlp(text).sents]
        opts = opts.copy()
        opts.split_sentences = False
        opts.read_prompts = False
        opts.prompt = prompt
        get = geput.get_list(sentences)
        speak_lines(get, out=out, synth=synth, postproc=postproc, opts=opts)
        if opts.echo:
            print()
        return

    if not synth:
        synth = get_synth(opts.model, opts)

    # echo the prompt and text
    if opts.echo_prompt:
        print(prompt, end="\t")
    if opts.echo:
        print(text, end="")
    if opts.echo_prompt or opts.echo:
        print()

    with SpeakContext(deafen=opts.deafen, loud_while_speaking=opts.loud_while_speaking):
        if text.strip() == "":
            time.sleep(opts.blank_line_silence)
            return

        # create a temporary file to store the audio output
        out_is_temp = not out
        if out_is_temp:
            with tempfile.NamedTemporaryFile(prefix="speak_", suffix=".wav", delete=False) as f:
                out = f.name
        try:
            # generate speech from the input text
            file, audio, rate = synth(text, out=out, prompt=prompt)

            rate_pp = rate
            if postproc:
                audio, rate_pp = postproc(file, audio, rate)

            if opts.deafen:
                sd.wait()
                amixer.sset("Capture", "nocap")
                logger.debug("Mic off")

            # play the audio
            if opts.play:
                sd.wait()

                sd.play(audio, samplerate=rate_pp)

        except AssertionError as e:
            if "No text" in str(e):
                time.sleep(opts.blank_line_silence)
            else:
                raise e
        except ZeroDivisionError as e:
            logger.error("speak_line: ignoring ZeroDivisionError: %r", e)
        finally:
            # Re-enable the microphone and clean up any temporary file
            if opts.deafen:
                sd.wait()
                amixer.sset("Capture", "cap")
                logger.debug("Mic on")
            if out_is_temp:
                os.remove(out)

        if opts.play and opts.wait:
            sd.wait()


def speak_lines(get, out=None, synth=None, postproc=None, opts=None):
    """Speak lines of text"""
    if not synth:
        synth = get_synth(opts.model, opts)

    if out:
        stem, ext = os.path.splitext(out)

    logger.info("ready to speak lines")

    inp = geput.input(get)

    i = 0
    while (line := inp()) is not None:
        logger.debug("speak_lines: line: %r", line)

        if out:
            output_file = f"{stem}_{i:06d}{ext}"
        else:
            output_file = None

        speak_line(
            text=line,
            out=output_file,
            synth=synth,
            postproc=postproc,
            opts=opts,
        )

        i += 1

    if opts.play and opts.wait:
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


class SpeakOptions(BaseModel):
    """SpeakOptions: a class that holds the options for the speak tool"""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    out: str | None = None
    text: str | None = None
    model: str = DEFAULT_MODEL
    silence: float = 0.1
    play: bool = True
    wait: bool = True
    deafen: bool = False
    tempo: float = 1.0
    pitch: float = 0.0
    list_models: bool = False
    cpu: bool = False
    download_all_models: bool = False
    echo: bool = True
    loud_while_speaking: int = 100
    prompt: str | None = None
    blank_line_silence: float = 0.5
    read_prompts: bool = False
    read_prompts_add: bool = False
    echo_prompt: bool = False
    split_sentences: bool = False
    nlp: spacy.Language|None = None
    compile: str = "none"  # "reduce-overhead"
    continue_: bool = False


def spacy_load(model: str) -> spacy.Language:
    """Load a spacy language model, downloading it if necessary."""
    try:
        return spacy.load(model)
    except OSError:
        spacy.cli.download(model)  # type: ignore
        return spacy.load(model)


def speak(
    get: geput.Get,
    opts: SpeakOptions,
    out: TextIO|None = None,
) -> None:
    """Speak text using the specified TTS model and options."""
    if not opts.cpu and not torch.cuda.is_available():
        opts.cpu = True

    if opts.download_all_models:
        download_all_coqui_models()
        sys.exit(0)

    add_parler_models()
    add_gtts_models()
    add_coqui_models()
    if opts.list_models:
        do_list_models()
        sys.exit(0)

    if opts.split_sentences:
        opts.nlp = spacy_load("en_core_web_sm")

    # parler compile options
    if opts.compile == "0":
        opts.compile = "none"
    elif opts.compile == "1":
        opts.compile = "default"
    elif opts.compile == "2":
        opts.compile = "reduce-overhead"

    synth = get_synth(opts.model, opts)

    # TODO put various options into a dict or something so we can pass them around more easily

    # Play an optional short silence to wake up the speakers
    if opts.silence > 0 and opts.play:
        sd.wait()
        rate = 44100
        silence_samples = int(opts.silence * rate)
        silent_audio = np.zeros(silence_samples)
        sd.play(silent_audio, samplerate=rate)

    postproc = None
    if opts.tempo != 1 or opts.pitch != 0:
        postproc = partial(postproc_soundstretch, tempo=opts.tempo, pitch=opts.pitch)

    if opts.text:
        logger.info("speak: text: %r", opts.text)
        speak_line(out, text=opts.text, synth=synth, postproc=postproc, opts=opts)
    if not opts.text or opts.continue_:
        logger.info("speak: reading from stdin")
        speak_lines(get, out, synth=synth, postproc=postproc, opts=opts)


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
    arg("--cpu", action="store_true", help="Use CPU rather than CUDA")
    arg("--download-all-models", action="store_true", help="Download all Coqui TTS models")
    arg("--no-echo", dest="echo", action="store_false", help="Don't echo text to stdout")
    arg("--loud-while-speaking", type=int, help="Volume level while speaking")
    arg("--prompt", help="Prompt text for Parler TTS")
    arg("--read-prompts", action="store_true", help="Read prompts from first column of TSV")
    arg("--read-prompts-add", action="store_true", help="Read prompts from first column of TSV and add to the base prompt")
    arg("--blank-line-silence", type=float, help="Duration of silence for blank lines")
    arg("--echo-prompt", action="store_true", help="Echo the prompt for each line")
    arg("--split-sentences", action="store_true", help="Split sentences into separate lines")
    arg("--compile", choices=["none", "default", "reduce-overhead", "0", "1", "2"], help="Compile model for speed")
    arg("--continue", dest="continue_", action="store_true", help="Continue speaking from stdin after saying the text")
    arg("text", nargs="?", help="Text to speak")


if __name__ == "__main__":
    main.go(speak, setup_args)
    sd.wait()


# TODO:

# As of 2024-11-25, Parler large-v1 breaks on the latest version of parler-tts
# and 1.1 models don't work on the older version. Hopefully they fix it soon.
# Also, compilation seems to work, but makes things slower! It uses a lot of CPU.

# - check out https://github.com/nateshmbhat/pyttsx3
# - try other Coqui TTS models and options
# - maybe use an OO approach
# - maybe port to Mac, Windows (mixer stuff)
# - coqui speaker selection

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
