#!/usr/bin/env python3-allemande

# version: 0.1.1

import os
import sys
import logging
import time

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import torch
import soundfile as sf

from omnivoice import OmniVoice

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def load_model():
    """Load the OmniVoice model and return it."""
    model = OmniVoice.from_pretrained(
        "k2-fsa/OmniVoice",
        device_map="cuda:0",
        dtype=torch.float16
    )
    # Apple Silicon users: use device_map="mps" instead
    # Intel Arc GPU users: use device_map="xpu" instead
    return model


def unload_model(model):
    """Unload the model from GPU memory."""
    del model
    torch.cuda.empty_cache()


def load_text(path):
    with open(path) as f:
        text = f.read()
    return text


def generate_audio(model, text, out_path):
    """Generate audio for the given text and write to out_path."""
    audio = model.generate(
        text=text,
        # instruct="female, british accent",
        ref_audio="ref.mp3",
        ref_text=load_text("ref.txt"),
    ) # audio is a list of `np.ndarray` with shape (T,) at 24 kHz.
    # If you don't want to input `ref_text` manually, you can directly omit the `ref_text`.
    # The model will use Whisper ASR to auto-transcribe it.
    sf.write(out_path, audio[0], 24000)


def main():
    """Read lines from stdin, generate audio for each, timing load vs generation."""
    print(load_text("ref.txt"))
    model = load_model()
    for i, line in enumerate(sys.stdin):
        text = line.rstrip("\n")
        if not text:
            continue

        out_path = f"out{i:04d}.mp3"
        t0 = time.time()

        # model = load_model()
        t1 = time.time()

        generate_audio(model, text, out_path)
        t2 = time.time()

        # unload_model(model)

        logger.info(
            "%s: load=%.2fs generate=%.2fs total=%.2fs",
            out_path, t1 - t0, t2 - t1, t2 - t0
        )


if __name__ == "__main__":
    main()

# Notes:
# - Unloading via `del model` + `torch.cuda.empty_cache()` is the standard HuggingFace approach; if OmniVoice holds internal references elsewhere it may not fully free VRAM — worth monitoring with `nvidia-smi`.
# - The `instruct` and ref audio params are hardcoded; you may want to make them configurable (e.g. env vars or a prefix syntax in stdin lines).
