#!/usr/bin/env python3

""" Use an LLM for text completion. """

import os
import re
import asyncio
from watchfiles import awatch
from threading import Thread

os.environ["HF_HUB_OFFLINE"] = "1"

import sys
from typing import TextIO

import torch
import transformers  # type: ignore

from ally import main, filer  # type: ignore

__version__ = "0.1.9"

logger = main.get_logger()

default_local_model: str = "default"
default_model: str = str(filer.resource(f"models/llm/{default_local_model}"))


def get_pipeline(model: str) -> transformers.pipeline:
    """Get the pipeline for the given model."""
    tokenizer = transformers.AutoTokenizer.from_pretrained(model)
    return transformers.pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        model_kwargs={"torch_dtype": torch.bfloat16},
        device_map="auto",
    )


def read_file(filename: str) -> str:
    """Read the given file."""
    if not os.path.exists(filename):
        return ""
    with open(filename, "r") as f:
        return f.read()


def append_to_file(filename: str, text: str):
    """Append text to the file."""
    with open(filename, "a") as f:
        f.write(text)


async def generate_response(pipeline, prompt: str, generation_kwargs: dict, stream: bool, stop_pattern: str = None):
    """Generate a response to the given prompt."""
    if stream:
        async for chunk in stream_pipeline_output(pipeline, prompt, generation_kwargs, stop_pattern):
            yield chunk
    else:
        result = await asyncio.to_thread(pipeline, prompt, **generation_kwargs)
        text = result[0]["generated_text"][len(prompt):]
        yield text


async def stream_pipeline_output(pipeline, prompt: str, generation_kwargs: dict, stop_pattern: str = None):
    """Stream the output of the pipeline."""
    streamer = transformers.TextIteratorStreamer(pipeline.tokenizer, skip_prompt=True)
    generation_kwargs["text_inputs"] = prompt
    generation_kwargs["streamer"] = streamer

    thread = Thread(target=pipeline, kwargs=generation_kwargs)
    thread.start()

    accumulated_text = ""
    for chunk in streamer:
        accumulated_text += chunk
        yield chunk
        if stop_pattern and re.search(stop_pattern, accumulated_text):
            break

    thread.join()


async def complete(
    file: str,
    model: str = default_model,
    stream: bool = True,
    context: int | None = float('inf'),
    temperature: float = 0.7,
    top_k: int | None = None,
    top_p: float | None = None,
    repetition_penalty: float | None = None,
    length: int | None = 50,
    watch: bool = False,
    first: bool = False,
    stop: str | None = None,
    echo: bool = True,
) -> None:
    """
    Complete text in a file using a local LLM model.
    """
    pipeline = get_pipeline(model)

    generation_kwargs = {
        "temperature": temperature,
        "top_k": top_k,
        "top_p": top_p,
        "repetition_penalty": repetition_penalty,
        "max_new_tokens": length,
    }

    async def process_file():
        text = read_file(file)

        ends_with_newline = text.endswith('\n')
        lines = text.splitlines()
        if context < float('inf'):
            lines = lines[-context:]
        prompt = "\n".join(lines)
        if ends_with_newline:
            prompt += "\n"

        completion = ""
        async for chunk in generate_response(pipeline, prompt, generation_kwargs, stream, stop):
            completion += chunk
            if echo and stream:
                print(chunk, end="", flush=True)
            if stream:
                append_to_file(file, chunk)

        if echo and not stream:
            print(completion, end="", flush=True)

        if not stream:
            append_to_file(file, completion)

    if first or not watch:
        await process_file()

    if watch:
        while True:
            watcher = awatch(file)
            async for changes in watcher:
                await process_file()
                break


def setup_args(arg):
    arg("file", help="the file to be completed")
    arg("--model", "-m", help="the model to use")
    arg("--no-stream", dest="stream", action="store_false", help="Enable streaming output")
    arg("--context", type=int, help="Number of lines to use for context")
    arg("--temperature", type=float, help="Temperature for text generation")
    arg("--top_k", type=int, help="Top k for text generation")
    arg("--top_p", type=float, help="Top p for text generation")
    arg("--repetition_penalty", type=float, help="Repetition penalty for text generation")
    arg("--length", "-l", type=int, help="Maximum number of new tokens to generate")
    arg("--watch", "-w", action="store_true", help="Watch file for changes")
    arg("--first", action="store_true", help="Run AI immediately at startup")
    arg("--stop", "-s", help="Regexp for stopping criteria (only in streaming mode)")
    arg("--no-echo", "-q", dest="echo", action="store_false", help="Do not echo the generated text")


if __name__ == "__main__":
    main.go(complete, setup_args)
