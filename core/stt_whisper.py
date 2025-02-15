#!/usr/bin/env python3-allemande

""" allemande - core whisper module """

import sys
import os
import logging
from pathlib import Path
from functools import partial
from types import SimpleNamespace

import inotify.adapters
import torch
import yaml
import whisper

os.environ["TRANSFORMERS_OFFLINE"] = "1"

import transformers

from ally import main, filer, logs, unix, util

logger = logs.get_logger()


prog = main.prog_info()

portals_dir = Path(os.environ["ALLEMANDE_PORTALS"])/prog.name


def gen(config, audio_file, *_args, model=None, **_kwargs):
    """ Transcribe text from an audio file. """

    language = config.get("language", None)

    result = model.transcribe(str(audio_file), language=language)

    response = {
        "text.txt": result["text"],
        "result.yaml": yaml.safe_dump(result),
    }

    return response


def load(portals, d, filename):
    """ Load a file from a directory or above """
    while True:
        f = d/filename
        if f.exists():
            return f.read_text(encoding="utf-8")
        if d == portals:
            break
        p = d.parent
        if p == d:
            break
        d = p
    f = prog.dir/filename
    if f.exists():
        return f.read_text(encoding="utf-8")
    raise FileNotFoundError(f"load: could not find {filename} in {d} or above")


def process_request(portals, port, req, fn, *args, **kwargs):
    """ Process a request on a port """
    port = Path(port)
    logger.info("%s:%s - processing", port, req)
    log_handler = None
    try:
        d = port/"doing"/req
        os.rename(port/"todo"/req, d)
        log_handler = logging.FileHandler(d/"log.txt")
        logger.addHandler(log_handler)

        config = yaml.safe_load(load(portals, d, "config.yaml"))
        request = d/"request.aud"
        response = fn(config, request, *args, **kwargs)
        for k, v in response.items():
            (d/k).write_text(v, encoding="utf-8")
        os.rename(d, port/"done"/req)
        logger.info("%s:%s - done", port, req)
    except Exception as e:
        logger.exception("%s:%s - error: %s", port, req, e)
        try:
            os.rename(d, port/"error"/req)
        except Exception as e2:
            logger.exception("%s:%s - error: %s", port, req, e2)
        if 'CUDA error' in str(e):
            raise
    finally:
        if log_handler:
            logger.removeHandler(log_handler)


def serve_requests(portals: str, model: str = "medium.en", poll_interval: float = 0.1):
    """ Serve requests from a directory of directories """
    the_model = whisper.load_model(model)
    fn = partial(gen, model=the_model)

    logger.info("serving requests from %s", portals)

    known_requests = find_todo_requests(portals)
    for portal, req in known_requests:
        logger.debug("Initial request detected: %s in %s", req, portal)
        await process_request(portals, portal, req, fn)

    known_requests_set = set(known_requests)

    while True:
        new_requests = find_todo_requests(portals)
        for portal, req_name in new_requests:
            if (portal, req_name) in known_requests_set:
                continue
            logger.debug("New request detected: %s in %s", req_name, portal)
            await process_request(portals, portal, req_name, fn)

        known_requests_set = set(new_requests)

        # Wait before next poll
        await asyncio.sleep(poll_interval)


def setup_args(arg):
    """Set up the command-line arguments"""
    arg("-p", "--portals", help="Directory of portals")
    arg("-i", "--poll-interval", type=float, help="Polling interval in seconds")
    arg("-m", "--model", help="Model to use")


if __name__ == "__main__":
    main.go(serve_requests, setup_args)
