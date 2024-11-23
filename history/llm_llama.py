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

import argh
import inotify.adapters
import torch
import yaml

os.environ["TRANSFORMERS_OFFLINE"] = "1"

import transformers  # pylint: disable=wrong-import-position

logger = logging.getLogger(__name__)


# TODO move to a library, allemande.py?
def prog_info():
    """Get info about the program"""
    prog = SimpleNamespace()
    prog.path = Path(__file__)
    prog.dir = prog.path.parent
    prog.filename = prog.path.name
    prog.name = prog.path.stem
    return prog


PROG = prog_info()

ports_dir = Path(os.environ["ALLEMANDE_PORTALS"]) / PROG.name
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
    model.tokenizer = transformers.LlamaTokenizer.from_pretrained(model_path, legacy=False)
    model.stopping_criteria = TokenStoppingCriteria(model.tokenizer, ["\n"])
    return model


# You can use this class in the following ways:
#
# 1. For single newline stopping:
# ```python
# stopping_criteria = TokenStoppingCriteria(tokenizer, ["\n"])
# ```
#
# 2. For double newline stopping (equivalent to your original implementation):
# ```python
# stopping_criteria = TokenStoppingCriteria(tokenizer, ["\n\n"])
# ```
#
# 3. For stopping on multiple possible tokens:
# ```python
# stopping_criteria = TokenStoppingCriteria(tokenizer, ["\n", ".", "?", "!"])

# TODO stream the response and check the end of generated text; stopping criteria are complex, unreliable and can corrupt the generation
# refer to chat/chat2.py


class TokenStoppingCriteria(transformers.StoppingCriteria):
    def __init__(self, tokenizer, stop_tokens):
        self.tokenizer = tokenizer
        self.stop_tokens = [tokenizer.encode(token, add_special_tokens=False) for token in stop_tokens]

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        for stop_token in self.stop_tokens:
            if input_ids[0][-len(stop_token) :].tolist() == stop_token:
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


def load(ports, d, filename):
    """Load a file from a directory or above"""
    while True:
        f = d / filename
        if f.exists():
            return f.read_text(encoding="utf-8")
        if d == ports:
            break
        p = d.parent
        if p == d:
            break
        d = p
    f = PROG.dir / filename
    if f.exists():
        return f.read_text(encoding="utf-8")
    raise FileNotFoundError(f"load: could not find {filename} in {d} or above")


def process_request(ports, port, req, fn, *args, **kwargs):
    """Process a request on a port"""

    def try_rename(src, dst):
        try:
            os.rename(src, dst)
        except Exception as e2:  # pylint: disable=broad-except
            logger.exception("%s:%s - error: %s", port, req, e2)

    port = Path(port)
    logger.info("%s:%s - processing", port, req)
    log_handler = None
    try:
        d = port / "doing" / req
        os.rename(port / "todo" / req, d)
        log_handler = logging.FileHandler(d / "log.txt")
        logger.addHandler(log_handler)

        config = yaml.safe_load(load(ports, d, "config.yaml"))
        request = load(ports, d, "request.txt")
        response = fn(config, request, *args, **kwargs)
        for k, v in response.items():
            (d / k).write_text(v, encoding="utf-8")
        os.rename(d, port / "done" / req)
        logger.info("%s:%s - done", port, req)
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("%s:%s - error: %s", port, req, e)

        # in case of CUDA error, CUDA out of memory:
        # exit now and retry the request later
        if re.search(r"\bCUDA\b", str(e)):
            try_rename(d, port / "todo" / req)
            raise e

        try_rename(d, port / "error" / req)
    finally:
        if log_handler:
            logger.removeHandler(log_handler)


# def port_setup(port):
# 	""" Set up a port """
# 	for box in ("prep", "todo", "doing", "done", "error", "history"):
# 		(port/box).mkdir(exist_ok=True)


def serve_requests_inotify(ports, fn):
    """Serve requests from a directory of directories"""
    logger.info("serving requests from %s", ports)
    i = inotify.adapters.Inotify()
    for port in Path(ports).iterdir():
        if not port.is_dir():
            continue
        # port_setup(port)
        todo = port / "todo"
        logger.info("watching %s", todo)
        i.add_watch(str(todo), mask=inotify.constants.IN_CREATE | inotify.constants.IN_MOVED_TO)
    for port in Path(ports).iterdir():
        if not port.is_dir():
            continue
        todo = port / "todo"
        for req in todo.iterdir():
            if not req.is_dir():
                continue
            process_request(ports, port, req.name, fn)
    for event in i.event_gen(yield_nones=False):
        (_, type_names, path, filename) = event
        logger.debug("PATH=[%r] FILENAME=[%r] EVENT_TYPES=%r", path, filename, type_names)
        port = Path(path).parent
        process_request(ports, port, filename, fn)


def serve_requests_poll(ports, fn, poll_interval=1.0):
    """Serve requests from a directory of directories using polling"""
    logger.info("serving requests from %s", ports)

    # Keep track of known requests across all ports
    known_requests = set()

    # Initial scan of existing requests
    for port in Path(ports).iterdir():
        if not port.is_dir():
            continue
        todo = port / "todo"
        logger.info("monitoring %s", todo)

        # Process existing requests
        for req in todo.iterdir():
            if not req.is_dir():
                continue
            known_requests.add((port, req.name))
            process_request(ports, port, req.name, fn)

    # Continuous polling loop
    while True:
        new_requests = set()

        # Scan all ports for new requests
        for port in Path(ports).iterdir():
            if not port.is_dir():
                continue
            todo = port / "todo"

            for req in todo.iterdir():
                if not req.is_dir():
                    continue
                new_requests.add((port, req.name))

        # Process any new requests that weren't known before
        for port, req_name in new_requests - known_requests:
            logger.debug("New request detected: %s in %s", req_name, port)
            process_request(ports, port, req_name, fn)

        # Update known requests
        known_requests = new_requests

        # Wait before next poll
        time.sleep(poll_interval)


def setup_logging(verbose, debug):
    """Setup logging"""
    log_level = logging.WARNING
    fmt = "%(message)s"
    if debug:
        log_level = logging.DEBUG
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s"
    elif verbose:
        log_level = logging.INFO
    logging.basicConfig(level=log_level, format=fmt)


def main(ports=str(ports_dir), model="default", verbose=False, debug=False, inotify=False):
    """main function"""
    setup_logging(verbose, debug)
    the_model = load_model(models_dir / model) if model else None
    fn = partial(gen, model=the_model)
    if inotify:
        serve_requests_inotify(ports, fn)
    else:
        serve_requests_poll(ports, fn)


if __name__ == "__main__":
    try:
        argh.dispatch_command(main)
    except KeyboardInterrupt:
        logger.info("interrupted")
        sys.exit(1)

# - The program uses a Transformer-based language model for text generation.
# - Main functions:
#  - load_model(): loads a pretrained model, tokenizer, and additional configurations
#  - gen(): generates new text based on the input and the configuration provided
#  - load(): loads a file from a directory or its parent directories
#  - process_request(): processes a request on a specified port, handles errors, and moves the request to the appropriate directory
#  - port_setup(): sets up directories for a given port
#  - serve_requests(): watches a directory for new requests and processes them using the provided function
#  - setup_logging(): sets up logging with different levels (verbose or debug)
#  - main(): loads the model if a path is provided, sets up partial function with the model, and serves requests
# - The program watches specified directories for incoming requests and processes them using the Transformer-based language model for text generation.
# - The generated text is saved in the respective directories based on the status of the request (e.g., "done" or "error").
