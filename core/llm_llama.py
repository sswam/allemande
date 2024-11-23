#!/usr/bin/env python3-allemande

""" allemande - core llama module """

import sys
import os
import logging
from pathlib import Path
from functools import partial
import re
import time

import inotify.adapters
import torch
import yaml

from ally import main, logs, filer, unix, util

os.environ["TRANSFORMERS_OFFLINE"] = "1"

import transformers  # pylint: disable=wrong-import-position


logger = logs.get_logger()

prog = main.prog_info()

portals_dir = Path(os.environ["ALLEMANDE_PORTALS"]) / prog.name
models_dir = Path(os.environ["ALLEMANDE_MODELS"]) / "llm"


def load_model(model_path, device_map="auto"):
    """Load a model"""
    model_path = str(model_path)
    model = transformers.LlamaForCausalLM.from_pretrained(
        model_path,
        device_map=device_map,
        torch_dtype=torch.float16,  # pylint: disable=no-member
        max_memory={0: "24GB"},
        low_cpu_mem_usage=True,
        cache_dir="cache",
    ).cuda()
    model.tokenizer = tokenizer = transformers.AutoTokenizer.from_pretrained(model_path)
    model.stopping_criteria = TokenStoppingCriteria(model.tokenizer, ["\n"])
#    transformers.LlamaTokenizer.from_pretrained(model_path, legacy=False)
#     model.stopping_criteria = TokenStoppingCriteriaRegexp(
#         model.tokenizer,
#         patterns=[r"^\w+: "],
#         window_size=32  # Adjust this value based on your needs
#     )
    return model


class TokenStoppingCriteria(transformers.StoppingCriteria):
    def __init__(self, tokenizer, stop_tokens):
        self.tokenizer = tokenizer
        self.stop_tokens = [tokenizer.encode(token, add_special_tokens=False) for token in stop_tokens]

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        for stop_token in self.stop_tokens:
            if input_ids[0][-len(stop_token):].tolist() == stop_token:
                return True
        return False


class TokenStoppingCriteriaRegexp(transformers.StoppingCriteria):
    def __init__(self, tokenizer, patterns, window_size=32):
        self.tokenizer = tokenizer
        self.patterns = [re.compile(pattern) for pattern in patterns]
        self.window_size = window_size

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        # Get the last window_size tokens and decode them
        last_tokens = input_ids[0][-self.window_size:].tolist()
        text = self.tokenizer.decode(last_tokens)

        # Check if any of the patterns match
        lines = text.split('\n')
        last_line = lines[-1] if lines else ""

        for pattern in self.patterns:
            # If it's a newline pattern, check directly
            if pattern.pattern == "\n" and text.endswith("\n"):
                return True
            # For other patterns, check against the last line
            elif pattern.search(last_line):
                return True

        return False


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

    tokenizer = model.tokenizer
    if "pad_token_id" not in config:
        config["pad_token_id"] = tokenizer.eos_token_id

    full_text = ""
    in_tokens = model.tokenizer(input_text, return_tensors="pt").input_ids.cuda()
    # n_in_tokens = in_tokens.shape[1]
    with torch.no_grad():
        gen_tokens = model.generate(
            in_tokens,
            stopping_criteria=transformers.StoppingCriteriaList([model.stopping_criteria]),
            **config,
        )
        if gen_tokens[0][-1] == tokenizer.eos_token_id:
            gen_tokens = gen_tokens[:, :-1]
        full_text = tokenizer.batch_decode(gen_tokens, skip_special_tokens=True)[0]
        if full_text.startswith(input_text):
            new_text = full_text[len(input_text) :]
        else:
            logger.warning("gen: full_text does not start with input_text. Will append entire generation.")
            new_text = full_text
        # TODO might not match due to leading spaces or something, could strip both?

    response = {
        "new.txt": new_text,
        "full.txt": full_text,
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


def process_request(portals, portal, req, fn, *args, **kwargs):
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
        response = fn(config, request, *args, **kwargs)
        for k, v in response.items():
            (d / k).write_text(v, encoding="utf-8")
        os.rename(d, portal / "done" / req)
        logger.info("%s:%s - done", portal, req)
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("%s:%s - error: %s", portal, req, e)

        # in case of CUDA error, CUDA out of memory:
        # exit now and retry the request later
        if re.search(r"\bCUDA\b", str(e)):
            try_rename(d, portal / "todo" / req)
            raise e

        try_rename(d, portal / "error" / req)
    finally:
        if log_handler:
            logger.removeHandler(log_handler)


# def portal_setup(portal):
# 	""" Set up a portal """
# 	for box in ("prep", "todo", "doing", "done", "error", "history"):
# 		(portal/box).mkdir(exist_ok=True)


def serve_requests_inotify(portals, fn):
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
            process_request(portals, portal, req.name, fn)
    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event
        logger.debug("PATH=[%r] FILENAME=[%r] EVENT_TYPES=%r", path, filename, type_names)
        portal = Path(path).parent
        process_request(portals, portal, filename, fn)


def serve_requests_poll(portals, fn, poll_interval=1.0):
    """Serve requests from a directory of directories using polling"""
    logger.info("serving requests from %s", portals)

    # Keep track of known requests across all portals
    known_requests = set()

    # Initial scan of existing requests
    for portal in Path(portals).iterdir():
        if not portal.is_dir():
            continue
        todo = portal / "todo"
        logger.info("monitoring %s", todo)

        # Process existing requests
        for req in todo.iterdir():
            if not req.is_dir():
                continue
            known_requests.add((portal, req.name))
            process_request(portals, portal, req.name, fn)

    # Continuous polling loop
    while True:
        new_requests = set()

        # Scan all portals for new requests
        for portal in Path(portals).iterdir():
            if not portal.is_dir():
                continue
            todo = portal / "todo"

            for req in todo.iterdir():
                if not req.is_dir():
                    continue
                new_requests.add((portal, req.name))

        # Process any new requests that weren't known before
        for portal, req_name in new_requests - known_requests:
            logger.debug("New request detected: %s in %s", req_name, portal)
            process_request(portals, portal, req_name, fn)

        # Update known requests
        known_requests = new_requests

        # Wait before next poll
        time.sleep(poll_interval)


def llm_llama(portals=str(portals_dir), model="default", inotify=False):
    """main function"""
    the_model = load_model(models_dir / model) if model else None
    fn = partial(gen, model=the_model)
    if inotify:
        serve_requests_inotify(portals, fn)
    else:
        serve_requests_poll(portals, fn)


def setup_args(arg):
    """Set up the command-line arguments"""
    arg("-p", "--portals", help="Directory of portals")
    arg("-m", "--model", help="Model name or path")
    arg("-i", "--inotify", help="Use inotify")


if __name__ == "__main__":
    main.go(llm_llama, setup_args)


# - The program uses a Transformer-based language model for text generation.
# - Main functions:
#  - load_model(): loads a pretrained model, tokenizer, and additional configurations
#  - gen(): generates new text based on the input and the configuration provided
#  - load(): loads a file from a directory or its parent directories
#  - process_request(): processes a request on a specified portal, handles errors, and moves the request to the appropriate directory
#  - portal_setup(): sets up directories for a given portal
#  - serve_requests(): watches a directory for new requests and processes them using the provided function
#  - setup_logging(): sets up logging with different levels (verbose or debug)
#  - main(): loads the model if a path is provided, sets up partial function with the model, and serves requests
# - The program watches specified directories for incoming requests and processes them using the Transformer-based language model for text generation.
# - The generated text is saved in the respective directories based on the status of the request (e.g., "done" or "error").
