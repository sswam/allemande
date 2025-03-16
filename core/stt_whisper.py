#!/usr/bin/env python3-allemande


""" allemande - core whisper module """

import logging
import os
import subprocess
from pathlib import Path
import asyncio
import fcntl
import yaml
import errno
import re

from ally import main, logs

logger = logs.get_logger()


prog = main.prog_info()

portals_dir = Path(os.environ["ALLEMANDE_PORTALS"]) / prog.name

WHISPER_CPP = "/opt/whisper.cpp/whisper"
WHISPER_CPP_CPU = "/opt/whisper.cpp/whisper-cpu"
WHISPER_CPP_DIR = str(Path(WHISPER_CPP).parent)
GPU_MUTEX = Path(os.environ["ALLEMANDE_PORTALS"]) / "gpu_mutex"


def try_gpu_command(primary_command, fallback_command=None):
    with GPU_MUTEX.open("w") as lockfile:
        try:
            # Try to acquire the lock non-blocking
            fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            # Lock acquired successfully, run primary command
            result = subprocess.run(primary_command, check=True)
            return result
        except BlockingIOError as e:
            if e.errno != errno.EWOULDBLOCK:
                raise
            # Lock is held by another process
            if fallback_command:
                # Run fallback command without requiring the lock
                result = subprocess.run(fallback_command, check=True)
                return result
            else:
                raise RuntimeError("GPU is currently in use by another process")
        finally:
            # Only unlock if we actually got the lock
            try:
                fcntl.flock(lockfile.fileno(), fcntl.LOCK_UN)
            except IOError:
                pass


def gen(config, audio_file, *_args, model=None, **_kwargs):
    """Transcribe text from an audio file."""

    language = config.get("language", "auto")
    model = config.get("model", model)

    if not re.match(r"[\w-]+$", model):
        raise ValueError(f"Invalid model name: {model}")
    
    model_path = f"models/ggml-{model}.bin"
    gpu_command = [WHISPER_CPP, "-l", language, "-m", model_path, "-otxt", str(audio_file)]
    cpu_command = [WHISPER_CPP_CPU, "-t", "32", "-l", language, "-m", model_path, "-otxt", str(audio_file)]

    # Try to run with GPU, fall back to CPU if GPU is busy
    result = try_gpu_command(gpu_command, cpu_command)

    outfile = str(audio_file) + ".txt"
    text = Path(outfile).read_text(encoding="utf-8").strip()

    response = {
        "text.txt": text,
        #        "result.yaml": yaml.safe_dump(result),
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


async def process_request(portals, port, req, fn, *args, **kwargs):
    """Process a request on a port"""
    port = Path(port)
    logger.info("%s:%s - processing", port, req)
    log_handler = None
    try:
        d = port / "doing" / req
        os.rename(port / "todo" / req, d)
        log_handler = logging.FileHandler(d / "log.txt")
        logger.addHandler(log_handler)

        config = yaml.safe_load(load(portals, d, "config.yaml"))
        request = d / "request.aud"
        response = fn(config, request, *args, **kwargs)
        for k, v in response.items():
            (d / k).write_text(v, encoding="utf-8")
        os.rename(d, port / "done" / req)
        logger.info("%s:%s - done", port, req)
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("%s:%s - error: %s", port, req, e)
        try:
            os.rename(d, port / "error" / req)
        except Exception as e2:  # pylint: disable=broad-except
            logger.exception("%s:%s - error: %s", port, req, e2)
        if "CUDA error" in str(e):
            raise
    finally:
        if log_handler:
            logger.removeHandler(log_handler)


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


async def serve_requests(portals: str = str(portals_dir), model: str = "base", poll_interval: float = 0.1):
    """Serve requests from a directory of directories"""
    logger.info("serving requests from %s", portals)

    os.chdir(WHISPER_CPP_DIR)

    known_requests = find_todo_requests(portals)
    for portal, req in known_requests:
        logger.debug("Initial request detected: %s in %s", req, portal)
        await process_request(portals, portal, req, gen, model=model)

    known_requests_set = set(known_requests)

    while True:
        new_requests = find_todo_requests(portals)
        for portal, req_name in new_requests:
            if (portal, req_name) in known_requests_set:
                continue
            logger.debug("New request detected: %s in %s", req_name, portal)
            await process_request(portals, portal, req_name, gen, model=model)

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
