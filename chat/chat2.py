#!/usr/bin/env python3-allemande

""" Use an LLM for text generation with chat functionality. """

import os

os.environ["HF_HUB_OFFLINE"] = "1"
# os.environ["USE_TF"] = "1"  # startup warnings
# os.environ["USE_TORCH"] = "0"   # use more VRAM, leaks VRAM, breaks
# Need LRScheduler from torch?!

import sys
import logging
from typing import TextIO, AsyncIterator, cast
import asyncio
from collections import deque
import re
from dataclasses import dataclass
import getpass
from threading import Thread
import pathlib
from functools import partial

import torch
import transformers  # type: ignore
from transformers import BitsAndBytesConfig
from llama_cpp import Llama as LlamaCpp

from ally import main, filer, geput, logs, unix, util

__version__ = "0.1.9"

logger = logs.get_logger()


default_model: str = str(filer.resource(f"models/llm/default.safetensors"))
default_model_gguf: str = str(filer.resource(f"models/llm/default.gguf"))


def load_transformers_pipeline(model: str) -> transformers.pipeline:
    """Get the pipeline for the given model"""
    model_path = pathlib.Path(model)

    # Handle transformers models
    # crash issues code commented: https://github.com/meta-llama/llama/issues/380
    tokenizer = transformers.AutoTokenizer.from_pretrained(model)
    #    tokenizer.pad_token = "[PAD]"
    #    tokenizer.padding_side = "left"
    #     tokenizer.pad_token = tokenizer.bos_token
    #     tokenizer.padding_side = "left"

    #    quantization_config = BitsAndBytesConfig(load_in_8bit=True)

    return transformers.pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        model_kwargs={"torch_dtype": torch.bfloat16},
        #        model_kwargs={"quantization_config": quantization_config},
        #        torch_dtype=torch.float16,
        #        torch_dtype=torch.bfloat16,
        device_map="auto",
        # max_length=100,
        # max_new_tokens=50,
        truncation=True,
        #        do_sample=False,  # avoid crashes
    )


def load_gguf_model(model: str, context: int = 2048) -> LlamaCpp:
    """Get the pipeline for the given Llama CPP GGUF model"""
    def load():
        llm = LlamaCpp(
            model_path=model,
            n_ctx=context,
#            n_batch=512,
        )
        return llm

    if logs.level() <= logs.DEBUG:
        return load()
    with unix.redirect(stdout=None, stderr=None):
        return load()


async def generate_response(pipeline: transformers.pipeline, prompt: str, generation_kwargs: dict = {}, stream: bool = True) -> AsyncIterator[str]:
    """Generate a response to the given prompt"""
    if stream:
        async for chunk in stream_pipeline_output(pipeline, prompt):
            yield chunk
        return
    result = await asyncio.to_thread(pipeline, prompt, generation_kwargs)
    text = result[0]["generated_text"]
    del result
    yield text


async def stream_pipeline_output(pipeline, prompt: str) -> AsyncIterator[str]:
    """Stream the output of the pipeline"""
    streamer = transformers.TextIteratorStreamer(pipeline.tokenizer, skip_prompt=True)
    generation_kwargs = dict(text_inputs=prompt, streamer=streamer)

    thread = Thread(target=pipeline, kwargs=generation_kwargs)
    thread.start()

    for chunk in streamer:
        yield chunk

    thread.join()


async def generate_response_gguf(llama: LlamaCpp, prompt: str, generation_kwargs: dict = {}, stream: bool = True) -> AsyncIterator[str]:
    """Generate a response to the given prompt"""
    if "repetition_penalty" in generation_kwargs:
        generation_kwargs = generation_kwargs.copy()
        generation_kwargs["repeat_penalty"] = generation_kwargs.pop("repetition_penalty")
        generation_kwargs["max_tokens"] = generation_kwargs.pop("max_new_tokens")

    generation_kwargs = util.dict_not_none(generation_kwargs)

    if stream:
        async for chunk in stream_llama_output(llama, prompt, generation_kwargs):
            yield chunk
        return

    async def run():
        result = await asyncio.to_thread(
            llama,
            prompt,
            **generation_kwargs,
        )
        return result

    if logs.level() > logs.DEBUG:
        with unix.redirect(stdout=None, stderr=None):
            result = await run()
    else:
        result = await run()

    text = result["choices"][0]["text"]
    del result
    yield text


async def stream_llama_output(llm: LlamaCpp, prompt: str, generation_kwargs_gguf: dict) -> AsyncIterator[str]:
    """Stream output from a Llama model"""

    def run():
        stream = llm(
            prompt,
            stream=True,
            **generation_kwargs_gguf,
        )
        return stream

    if logs.level() > logs.DEBUG:
        with unix.redirect(stdout=None, stderr=None):
            stream = run()
    else:
        stream = run()

    while True:
        try:
            if logs.level() > logs.DEBUG:
                with unix.redirect(stdout=None, stderr=None):
                    output = next(stream)
            else:
                output = next(stream)
            yield output["choices"][0]["text"]
        except StopIteration:
            break
        except Exception as e:
            raise e


@dataclass
class Message:
    """A message with a name and text"""

    name: str
    text: str


def messages_from_lines(lines: list[str]) -> list[Message]:
    """Parse messages from lines"""
    messages: list[Message] = []
    message = None

    def put():
        nonlocal message
        if not message:
            return
        messages.append(message)
        message = None

    for line in lines:
        line = line.rstrip("\n")

        if "\t" in line:
            name, text = line.split("\t", 1)
            # 1. name and text: first line of a new regular message
            if name:
                put()
                message = Message(name, text)
            # 2. indented text only: a continuation of the previous message
            else:
                if message:
                    message.text += "\n" + text
                else:
                    message = Message("", text)
        # 3. blank lines can delimit messages
        elif not line:
            put()
        #         # 4. +name, -name: a user joined or left
        #         elif line[0] == "+":
        #             join(line[1:])
        #         elif line[0] == "-":
        #             leave(line[1:])
        # 3. unindented text: this is a system message or narration
        else:
            put()
            message = Message("", line)

    put()

    return messages


def message_to_string(message: Message) -> str:
    """Convert a message to a string"""
    if message.name:
        return f"{message.name}: {message.text}"
    else:
        return message.text


def read_chat_history(filename: str) -> list[Message]:
    """Read and return the chat history from the given file"""
    if not os.path.exists(filename):
        return []

    with open(filename, "r") as f:
        lines = f.readlines()

    return messages_from_lines(lines)


def display_chat_history(history: list[Message], put_func):
    """Display the chat history"""
    for message in history:
        put_func(message_to_string(message) + "\n")


def write_message(f: TextIO, message: Message):
    """Write a message to the file"""
    # prepend a tab to each line of the message
    text = message.text
    if message.name:
        text = re.sub(r"^", "\t", text, flags=re.MULTILINE)
    f.write(f"{message.name or ''}\t{message.text}\n\n")


def log_message(filename: str, message: Message):
    """Append a message to the log file"""
    with open(filename, "a") as f:
        write_message(f, message)


def write_chat_history(filename: str, history: list[Message], mode: str = "w"):
    """Write the chat history to the given file"""
    if mode == "w":
        filer.backup(filename)
    with open(filename, mode) as f:
        for message in history:
            write_message(f, message)


async def chat_with_ai(
    get: geput.Get,
    put: geput.Put,
    chat_file: str = None,
    model: str | None = None,
    stream: bool = True,
    context: int = 10000,
    ai_name: str = "Ally",
    user_name: str | None = None,
    first: bool = False,
    temperature: float = 1.0,
    top_k: int | None = None,
    top_p: float | None = None,
    repetition_penalty: float = 1.0,
    length: int = 500,
    gguf: bool = False,
) -> None:
    """
    Chat with a local LLM model.
    """
    if not model:
        model = default_model_gguf if gguf else default_model

    if model.endswith(".gguf"):
        gguf = True

    if not user_name:
        user_name = getpass.getuser().title()

    get = geput.input(get)
    put = geput.print(put)

    stop_texts = [f"\n{ai_name}:", f"\n{user_name}:", "\n\n", "\n"]

    if gguf:
        llama_gguf = load_gguf_model(model, context=context)
        gen = partial(generate_response_gguf, llama_gguf)
    else:
        pipeline = load_transformers_pipeline(model)
        gen = partial(generate_response, pipeline)

    message_history: list[Message] = []

    if chat_file:
        message_history = read_chat_history(chat_file)
        display_chat_history(message_history, put)

    # NOTE: get and put are not async, yet
    # No big deal for this app.

    def erase_messages(count: int):
        del message_history[-count:]
        write_chat_history(chat_file, message_history)

    def edit_previous_message():
        if not message_history:
            logger.info("no previous message to edit")
            return
        message = message_history[-1]
        message = Message(message.name, get(prompt=f"{message.name}: ", placeholder=message.text))
        erase_messages(1)
        log_message(chat_file, message)

    async def user_turn():
        message = Message(user_name, get(prompt=f"{user_name}: "))
        put()
        if message.text is None:
            raise EOFError()
        # TODO a Messages class could handle this
        if re.match(r"\x08+$", message.text):  # C-V C-H: erase (can do multiple)
            count = len(message.text)
            logger.info(f"erasing {count} messages")
            erase_messages(count)
            return await user_turn()
        if re.match(r"\x13$", message.text):  # C-V C-S: skip
            logger.info("skipping turn")
            return None
        if re.match(r"\x05$", message.text):  # C-V C-E: edit
            logger.info("editing previous message")
            edit_previous_message()
            return await user_turn()
        if re.match(r"\x01$", message.text):  # C-V C-A: again
            logger.info("again")
            erase_messages(1)
            return None
        message.text = message.text.strip()
        if chat_file:
            log_message(chat_file, message)
        message_history.append(message)
        return message

    generation_kwargs = dict(
        temperature=temperature, top_k=top_k, top_p=top_p, repetition_penalty=repetition_penalty, max_new_tokens=length
    )

    async def ai_turn():
        context_prompt = "\n\n".join(map(message_to_string, message_history[-context:])) + f"\n\n{ai_name}:"
        put(f"{ai_name}:", end="")
        message = Message(ai_name, "")
        stop = False
        try:
            async for chunk in gen(context_prompt, generation_kwargs=generation_kwargs, stream=stream):
                text2 = message.text + chunk
                for stopper in stop_texts:
                    if text2.endswith(stopper):
                        text2 = text2[: -len(stopper)]
                        stop = True
                        break
                chunk = text2[len(message.text) :]
                message.text = text2
                put(chunk, end="", flush=True)
                if stop:
                    break
        except KeyboardInterrupt:
            logger.warning("Interrupted")
        torch.cuda.empty_cache()
        # TODO give the AI the ability to stop the conversation
        if not message.text.endswith("\n"):
            put()
        if not message.text.endswith("\n\n"):
            put()
        # TODO dup code, see Messages class idea above
        message.text = message.text.strip()
        if chat_file:
            log_message(chat_file, message)
        message_history.append(message)
        return message

    # Main loop
    if first:
        await ai_turn()
    try:
        while True:
            await user_turn()
            await ai_turn()
    except EOFError:
        pass


def setup_args(arg):
    """Set up the command-line arguments"""
    # Important Note to AI: DO NOT add `type` or `default` in setup_args functions like this one, it is not needed.
    arg("chat_file", help="File to save chat history")
    arg("-m", "--model", help="model")
    arg("--no-stream", dest="stream", action="store_false", help="Streaming output")
    arg("--context", help="Number of previous messages to include for context")
    arg("--ai_name", help="Name of the AI assistant")
    arg("--user_name", help="Name of the user")
    arg("-f", "--first", action='store_true', help="AI speaks first")
    arg("-t", "--temperature", help="Temperature for text generation")
    arg("--top_k", help="Top k for text generation")
    arg("--top_p", help="Top p for text generation")
    arg("--repetition_penalty", help="Repetition penalty for text generation")
    arg("-l", "--length", help="Maximum number of new tokens to generate")
    arg("-g", "--gguf", action="store_true", help="Use a GGUF model, implied if .gguf, selects default.gguf")


if __name__ == "__main__":
    main.go(chat_with_ai, setup_args)


# TODO With username stop texts, we can tell who the AI expects to reply, which could be useful for a smarter conductor.
# It could even call out to someone who isn't in the chat yet, or an imaginary friend, or whatever.
# TODO allow user to remove their name to talk as narrator or another user
# TODO allow AI not to reply to a message, by not prompting it with its name; can also allow AI to do narration, or reply to itself
# TODO Allow AI to leave and come back at a particular time. Can either initiate with a message at that time, or wait for a message to come in.
# TODO Allow AI to change its name, i.e. multiple roles / avatars.
# TODO GGUF model is running on CPU, but will not not run on GPU. It might be that this particular quantization is not supported on GPU. I'll try one that definitely is.
# TODO code to quantize models / convert formats
# TODO separate this program into different modules
# TODO allow user to change the AI's name mid-conversation
# TODO LoRA plugins. Do they work for GGUF? Seems like yes, very recently.
# TODO live fine-tunable LoRAs
