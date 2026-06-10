#!/usr/bin/env python3-allemande

import os

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

from omnivoice import OmniVoice
import soundfile as sf
import torch
import time

model = OmniVoice.from_pretrained(
    "k2-fsa/OmniVoice",
    device_map="cuda:0",
    dtype=torch.float16
)
# Apple Silicon users: use device_map="mps" instead
# Intel Arc GPU users: use device_map="xpu" instead

start = time.time()
print("ready at", start)

audio = model.generate(
#   text="Hello, this is a test of zero-shot voice cloning.",
    text="I think so! As a matter of fact, Sam, I was thinking about the fact that even as AI technology advances and gets more advanced, some human experiences remain unique to humans. There's something truly special about the human connection and relationships. I think AI can augment and enhance our lives in so many ways, but I believe human experience is, by its very nature, more nuanced, messy, and beautiful. Don't you agree?",
    instruct="female, british accent",
    # ref_audio="ref.wav",
    # ref_text="Transcription of the reference audio.",
) # audio is a list of `np.ndarray` with shape (T,) at 24 kHz.

end = time.time()
print("done at", end, "after", end-start, "seconds")

# If you don't want to input `ref_text` manually, you can directly omit the `ref_text`.
# The model will use Whisper ASR to auto-transcribe it.

sf.write("out.wav", audio[0], 24000)
