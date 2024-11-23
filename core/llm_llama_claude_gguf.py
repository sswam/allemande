Based on the example in chat2.py and the guidance, I'll improve llm_llama.py. Here's the updated version focusing on the main tasks:

```python
#!/usr/bin/env python3-allemande

""" allemande - core llama module """

import sys
import os
import logging
from pathlib import Path
from functools import partial
from types import SimpleNamespace
import re
import time
from threading import Thread
import asyncio

import argh
import inotify.adapters
import torch
import yaml
from llama_cpp import Llama

os.environ["TRANSFORMERS_OFFLINE"] = "1"

import transformers  # pylint: disable=wrong-import-position

__version__ = "0.1.3"

logger = logging.getLogger(__name__)


def prog_info():
    """Get info about the program"""
    prog = SimpleNamespace()
    prog.path = Path(__file__)
    prog.dir = prog.path.parent
    prog.filename = prog.path.name
    prog.name = prog.path.stem
    return prog


PROG = prog_info()

ports_dir = Path(os.environ["ALLEMANDE_PORTS"]) / PROG.name
models_dir = Path(os.environ["ALLEMANDE_MODELS"]) / "llm"


def load_model(model_path, device_map="auto"):
    """Load a transformers model"""
    model_path = str(model_path)
    
    if model_path.endswith('.gguf'):
        return load_model_gguf(model_path)
        
    tokenizer = transformers.AutoTokenizer.from_pretrained(model_path, legacy=False)
    model = transformers.LlamaForCausalLM.from_pretrained(
        model_path,
        device_map=device_map,
        torch_dtype=torch.float16,
        max_memory={0: "24GB"},
        low_cpu_mem_usage=True,
        cache_dir="cache",
    ).cuda()
    model.tokenizer = tokenizer
    return model


def load_model_gguf(model_path: str, context: int = 2048) -> Llama:
    """Load a GGUF model using llama.cpp"""
    return Llama(
        model_path=str(model_path),
        n_ctx=context,
    )


async def stream_generate(model, input_text: str, stoppers: list[str] | None = None) -> str:
    """Generate text by streaming and checking for stop sequences"""
    if stoppers is None:
        stoppers = ["\n", "\n\n"]
        
    if isinstance(model, Llama):
        return await stream_generate_gguf(model, input_text, stoppers)
        
    streamer = transformers.TextIteratorStreamer(model.tokenizer, skip_prompt=True)
    generation_kwargs = dict(
        text_inputs=input_text,
        streamer=streamer,
        max_new_tokens=100
    )

    thread = Thread(target=model, kwargs=generation_kwargs)
    thread.start()

    text = ""
    for chunk in streamer:
        text += chunk
        for stopper in stoppers:
            if text.endswith(stopper):
                thread.join()
                return text
                
    thread.join()
    return text


async def stream_generate_gguf(model: Llama, input_text: str, stoppers: list[str]) -> str:
    """Generate text from GGUF model by streaming and checking for stop sequences"""
    stream = model(input_text, stream=True, max_tokens=100)
    text = ""
    
    for output in stream:
        chunk = output["choices"][0]["text"]
        text += chunk
        for stopper in stoppers:
            if text.endswith(stopper):
                return text
                
    return text


def gen(config, input_text, *_args, model=None, **_kwargs):
    """Generate text from a model."""
    if model is None:
        return {
            "new.txt": "",
            "full.txt": input_text,
        }
    if config is None:
        config = {}

    if _args:
        logger.warning("gen: ignoring args: %s", _args)
    if _kwargs:
        logger.warning("gen: ignoring kwargs: %s", _kwargs)

    stoppers = config.get('stoppers', ["\n", "\n\n"])
    
    # Run async generation in event loop
    loop = asyncio.new_event_loop()
    full_text = loop.run_until_complete(stream_generate(model, input_text, stoppers))
    loop.close()

    if full_text.startswith(input_text):
        new_text = full_text[len(input_text):]
    else:
        logger.warning("gen: full_text does not start with input_text. Will append entire generation.")
        new_text = full_text

    response = {
        "new.txt": new_text,
        "full.txt": full_text,
    }

    return response

# Rest of the file unchanged...
```

Key changes:

1. Added GGUF model support via llama.cpp
2. Replaced stopping criteria with streaming and text matching
3. Added version number
4. Added support for configurable stop sequences
5. Made model loading handle both transformers and GGUF models

The changes focus on the main functionality while preserving the existing structure and error handling. I've kept all the logging and comments.

The command-line interface and request handling remain unchanged since they weren't part of the core requirements.

Let me know if you'd like me to elaborate on any part or make additional changes.

