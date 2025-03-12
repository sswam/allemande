#!/usr/bin/env python3-allemande

""" allemande - core llama module """

import os
import logging
from pathlib import Path
from functools import partial
import regex
import time
from typing import AsyncIterator, Iterator, cast
from threading import Thread
import asyncio

import inotify.adapters  # type: ignore
import torch
import yaml

from ally import main, logs, unix, util

os.environ["GGML_CUDA_ENABLE_UNIFIED_MEMORY"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

import transformers  # type: ignore # pylint: disable=wrong-import-order, wrong-import-position
from llama_cpp import Llama as LlamaCpp, CreateCompletionResponse # pylint: disable=wrong-import-order, wrong-import-position

__version__ = "0.2.2"


logger = logs.get_logger()

prog = main.prog_info()

portals_dir = Path(os.environ["ALLEMANDE_PORTALS"]) / prog.name
models_dir = Path(os.environ["ALLEMANDE_MODELS"]) / "llm"

default_model: str = str(models_dir/"default")
default_model_gguf: str = str(models_dir/"default.gguf")


# Matches a line that starts with a unicode 'name':
# 1. Starts with a letter
# 2. Followed by letters, numbers, or underscores
# 3. Ends with a colon
# 4. Followed by optional whitespace and end of line

transformers_prompt_cache = transformers.DynamicCache()


def load_transformers_pipeline(model: str) -> transformers.pipeline:
    """Get the pipeline for the given model"""

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
        use_cache=True,
        #        do_sample=False,  # avoid crashes
    )


def load_gguf_model(model: str, context: int = 131072, n_gpu_layers=-1) -> LlamaCpp:
    """Get the pipeline for the given Llama CPP GGUF model"""
    llm = LlamaCpp(
        model_path=model,
        n_ctx=context,
        n_gpu_layers=n_gpu_layers,
        n_batch=512,
    )
    return llm


async def stream_transformers(pipeline: transformers.Pipeline, prompt: str, generation_kwargs: dict|None = None) -> AsyncIterator[str]:
    """Stream the output of the transformers pipeline"""
    streamer = transformers.TextIteratorStreamer(pipeline.tokenizer, skip_prompt=True)
    generation_kwargs = {"text_inputs": prompt, "streamer": streamer, **(generation_kwargs or {})}

    thread = Thread(target=pipeline, kwargs=generation_kwargs)
    thread.start()

    for chunk in streamer:
        yield chunk

    thread.join()


async def stream_gguf(llm: LlamaCpp, prompt: str, generation_kwargs: dict) -> AsyncIterator[str]:
    """Stream output from a Llama model"""

    generation_kwargs = generation_kwargs.copy()
    generation_kwargs["repeat_penalty"] = generation_kwargs.pop("repetition_penalty", None)
    generation_kwargs["max_tokens"] = generation_kwargs.pop("max_new_tokens", None)

    for bad_arg in "early_stopping", "penalty_alpha":
        generation_kwargs.pop(bad_arg, None)

    generation_kwargs = util.dict_not_none(generation_kwargs)

    stream = cast(Iterator[CreateCompletionResponse], llm(
        prompt,
        stream=True,
        **generation_kwargs,
    ))

    while True:
        try:
            output = next(stream)
            yield output["choices"][0]["text"]
        except StopIteration:
            break


async def collect_response(streamer, model, config, input_text, *_args, **_kwargs):
    """Generate text from a model."""
    if model is None:
        return {
            "new.txt": "",
        }
    if config is None:
        config = {}

    stop_regexs = config.pop("stop_regexs", [])
    logger.debug("stop_regexs:")
    for i in range(len(stop_regexs)):
        logger.debug("`%s`", stop_regexs[i])
        stop_regexs[i] = regex.compile(stop_regexs[i])

    if _args:
        logger.warning("gen: ignoring args: %s", _args)
    if _kwargs:
        logger.warning("gen: ignoring kwargs: %s", _kwargs)

    log_level = logs.level()

    max_lines = config.pop("lines", None)

    logger.debug("max_lines: %s", max_lines)

    text = ""
    stop = False
    try:
        async for chunk in streamer(model, input_text, generation_kwargs=config):
            text2 = text + chunk

            if log_level <= logs.DEBUG:
                print(chunk, end="", flush=True)

            for stopper in stop_regexs:
                if match := stopper.search(text2):
                    logger.debug("Stopping at: `%s`", match.group())
                    logger.debug("Stopping regex: %s", stopper)
                    text2 = text2[:match.start()]
                    stop = True
                    break
            else:
                logger.debug("text2: %s", text2)
                if max_lines:
                    lines = text2.splitlines()
                    count = len([line for line in lines if line.strip()])
                    logger.debug("count: %s", count)
                    logger.debug("max_lines: %s", max_lines)
                    if count > max_lines:
                        while count > max_lines:
                            l = lines.pop()
                            if l.strip():
                                count -= 1
                        text2 = "\n".join(lines)
                        stop = True

            if stop:
                if log_level <= logs.DEBUG:
                    print()

            text = text2

            if stop:
                break
        else:
            if log_level <= logs.DEBUG:
                print()
    except KeyboardInterrupt:
        logger.warning("Interrupted")
    # torch.cuda.empty_cache()

    text = text.strip()

    response = {
        "new.txt": text,
    }

    return response


def load(portals, d, filename):
    """Load a file from a directory or above"""
    while True:
        f = d / filename
        if f.exists():
            return f.read_text(encoding="utf-8")
        if d == portals:
            break
        p = d.parent
        if p == d:
            break
        d = p
    f = prog.dir / filename
    if f.exists():
        return f.read_text(encoding="utf-8")
    raise FileNotFoundError(f"load: could not find {filename} in {d} or above")


async def process_request(portals, portal, req, gen, *args, **kwargs):
    """Process a request on a portal"""

    def try_rename(src, dst):
        try:
            os.rename(src, dst)
        except Exception as e2:  # pylint: disable=broad-except
            logger.exception("%s:%s - error: %s", portal, req, e2)

    portal = Path(portal)
    logger.info("%s:%s - processing", portal, req)
    log_handler = None
    try:
        d = portal / "doing" / req
        os.rename(portal / "todo" / req, d)
        log_handler = logging.FileHandler(d / "log.txt")
        logger.addHandler(log_handler)

        config = yaml.safe_load(load(portals, d, "config.yaml"))
        request = load(portals, d, "request.txt")
        response = await gen(config, request, *args, **kwargs)
        for k, v in response.items():
            (d / k).write_text(v, encoding="utf-8")
        os.rename(d, portal / "done" / req)
        logger.info("%s:%s - done", portal, req)
    except (Exception, KeyboardInterrupt, SystemExit) as e:  # pylint: disable=broad-except
        logger.exception("%s:%s - error: %s", portal, req, e)

        # in case of CUDA error, CUDA out of memory:
        # exit now and retry the request later
        if regex.search(r"\bCUDA\b", str(e)):
            try_rename(d, portal / "todo" / req)
            raise e

        try_rename(d, portal / "error" / req)
    finally:
        if log_handler:
            logger.removeHandler(log_handler)


async def serve_requests_inotify(portals: str, gen: callable):
    """Serve requests from a directory of directories"""
    logger.info("serving requests from %s", portals)
    i = inotify.adapters.Inotify()
    for portal in Path(portals).iterdir():
        if not portal.is_dir():
            continue
        # portal_setup(portal)
        todo = portal / "todo"
        logger.info("watching %s", todo)
        i.add_watch(str(todo), mask=inotify.constants.IN_CREATE | inotify.constants.IN_MOVED_TO)
    for portal in Path(portals).iterdir():
        if not portal.is_dir():
            continue
        todo = portal / "todo"
        for req in todo.iterdir():
            if not req.is_dir():
                continue
            logger.info("Initial request: %s in %s", req, portal)
            await process_request(portals, portal, req.name, gen)
    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event
        logger.debug("PATH=[%r] FILENAME=[%r] EVENT_TYPES=%r", path, filename, type_names)
        portal = Path(path).parent
        logger.info("New request: %s in %s", filename, portal)
        await process_request(portals, portal, filename, gen)


def find_todo_requests(portals: str = str(portals_dir)) -> list[tuple[Path, str]]:
    """Find all requests in the todo directories"""
    requests = []
    for portal in Path(portals).iterdir():
        if not portal.is_dir():
            continue
        todo = portal / "todo"
        for req in todo.iterdir():
            if not req.is_dir():
                continue
            requests.append((portal, req.name))
    requests.sort(key=lambda x: (x[0].stat().st_mtime, x[1]))
    return requests


async def serve_requests_poll(portals: str, gen: callable, poll_interval: float = 0.1):
    """Serve requests from a directory of directories using polling"""
    logger.info("serving requests from %s", portals)
    known_requests = find_todo_requests(portals)
    for portal, req in known_requests:
        logger.info("Initial request: %s in %s", req, portal)
        await process_request(portals, portal, req, gen)

    known_requests_set = set(known_requests)

    while True:
        new_requests = find_todo_requests(portals)
        for portal, req_name in new_requests:
            if (portal, req_name) in known_requests_set:
                continue
            logger.info("New request: %s in %s", req_name, portal)
            await process_request(portals, portal, req_name, gen)

        known_requests_set = set(new_requests)

        # Wait before next poll
        await asyncio.sleep(poll_interval)


async def llm_llama(portals:str =str(portals_dir), model: str|None = None, use_inotify: bool=False, gguf: bool=False, context: int=32*1024, n_gpu_layers: int=-1):
    """main function wrapper to suppress output from llama_cpp"""

    # redirect stdout and stderr to /dev/null if not in debug mode
    # because llama_cpp prints a lot of debug info
    # TODO Ideally we would want to always keep it in the log file,
    # and show it also on the console in debug mode. Later.
    if logs.level() <= logs.DEBUG:
        await llm_llama_main(portals, model, use_inotify, gguf, context, n_gpu_layers)
    with unix.redirect(stdout=None, stderr=None):
        await llm_llama_main(portals, model, use_inotify, gguf, context, n_gpu_layers)


async def llm_llama_main(portals: str, model: str|None, use_inotify: bool, gguf: bool, context=32*1024, n_gpu_layers=-1):
    """main function"""
    if not model:
        model = default_model_gguf if gguf else default_model
    elif "/" not in model:
        model = str(models_dir / model)

    if model.endswith(".gguf"):
        gguf = True

    if gguf:
        llama_gguf = load_gguf_model(model, context=context, n_gpu_layers=n_gpu_layers)
        gen = partial(collect_response, stream_gguf, llama_gguf)
    else:
        pipeline = load_transformers_pipeline(model)
        gen = partial(collect_response, stream_transformers, pipeline)

    if use_inotify:
        await serve_requests_inotify(portals, gen)
    else:
        await serve_requests_poll(portals, gen)


def setup_args(arg):
    """Set up the command-line arguments"""
    arg("-p", "--portals", help="Directory of portals")
    arg("-m", "--model", help="Model name or path")
    arg("-i", "--use-inotify", action="store_true", help="Use inotify")
    arg("-g", "--gguf", action="store_true", help="Use GGUF model")
    arg("-c", "--context", help="Context size")
    arg("-n", "--n-gpu-layers", help="Number of GPU layers to use for GGUF")


if __name__ == "__main__":
    main.go(llm_llama, setup_args)
