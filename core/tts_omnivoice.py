#!/usr/bin/env python3-allemande

"""Allemande - OmniVoice TTS service"""

import os
import asyncio
import logging
from pathlib import Path

import yaml
import torch
import soundfile as sf

# Must be set before transformers-based modules are imported
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from omnivoice import OmniVoice  # type: ignore

from ally import main, logs

__version__ = "0.1.0"

logger = logs.get_logger()

prog = main.prog_info()

portals_dir = Path(os.environ["ALLEMANDE_PORTALS"]) / prog.name
rooms_dir = Path(os.environ["ALLEMANDE_ROOMS"])


def load_model(device: str = "cuda:0") -> OmniVoice:
    """Load the OmniVoice model onto the specified device."""
    logger.info("loading OmniVoice model on %s", device)
    model = OmniVoice.from_pretrained(
        "k2-fsa/OmniVoice",
        device_map=device,
        dtype=torch.float16,
    )
    return model


def gen(config: dict, request_dir: Path, model: OmniVoice) -> None:
    """Generate speech audio from the text file in request_dir."""
    text = (request_dir / "request.txt").read_text(encoding="utf-8").strip()

    instruct = config.get("instruct")
    ref = config.get("ref")
    voice = config.get("voice")

    kwargs: dict = {"text": text}

    if instruct:
        kwargs["instruct"] = instruct

    if ref:
        ref_path = Path(ref)
        kwargs["ref_audio"] = str(request_dir / ref_path)
        kwargs["ref_text"] = (request_dir / ref_path.parent / f"{ref_path.stem}.txt").read_text(encoding="utf-8")
    elif voice:
        # XXX must implement access control here
        voice_path = Path(voice)
        kwargs["ref_audio"] = str(rooms_dir / voice_path)
        kwargs["ref_text"] = (rooms_dir / voice_path.parent / f"{voice_path.stem}.txt").read_text(encoding="utf-8")

    audio = model.generate(**kwargs)
    out_path = request_dir / "response.mp3"
    sf.write(str(out_path), audio[0], 24000)
    logger.info("wrote audio to %s", out_path)


def load(portals: Path, d: Path, filename: str) -> str:
    """Load a file from a directory or above, up to portals root."""
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


async def process_request(portals: Path, port: Path, req: str, model: OmniVoice) -> None:
    """Process a single TTS request, moving it through todo -> doing -> done/error."""
    logger.info("%s:%s - processing", port, req)
    log_handler = None
    d = port / "doing" / req
    try:
        os.rename(port / "todo" / req, d)
        log_handler = logging.FileHandler(d / "log.txt")
        logger.addHandler(log_handler)

        config = yaml.safe_load(load(portals, d, "config.yaml")) or {}
        gen(config, d, model)
        os.rename(d, port / "done" / req)
        logger.info("%s:%s - done", port, req)
    except Exception as e:  # pylint: disable=broad-except
        logger.exception("%s:%s - error: %s", port, req, e)
        try:
            os.rename(d, port / "error" / req)
        except Exception as e2:  # pylint: disable=broad-except
            logger.exception("%s:%s - could not move to error dir: %s", port, req, e2)
    finally:
        if log_handler:
            logger.removeHandler(log_handler)


def find_todo_requests(portals: Path) -> list[tuple[Path, str]]:
    """Find all pending requests across all portals."""
    requests = []
    for portal in portals.iterdir():
        if not portal.is_dir():
            continue
        todo = portal / "todo"
        if not todo.is_dir():
            continue
        for req in todo.iterdir():
            if not req.is_dir():
                continue
            requests.append((portal, req.name))
    requests.sort(key=lambda x: (x[0].stat().st_mtime, x[1]))
    return requests


async def serve_requests(
    portals: str = str(portals_dir),
    device: str = "cuda:0",
    poll_interval: float = 0.1,
) -> None:
    """Load the model and serve TTS requests from a directory of portals."""
    logger.info("serving TTS requests from %s", portals)

    portals_path = Path(portals)
    model = load_model(device)

    # Process any requests that were pending before startup
    known_requests = find_todo_requests(portals_path)
    for portal, req in known_requests:
        logger.debug("Initial request detected: %s in %s", req, portal)
        await process_request(Path(portals), portal, req, model=model)

    known_requests_set = set(known_requests)

    while True:
        new_requests = find_todo_requests(portals_path)
        for portal, req_name in new_requests:
            if (portal, req_name) in known_requests_set:
                continue
            logger.debug("New request detected: %s in %s", req_name, portal)
            await process_request(Path(portals), portal, req_name, model=model)

        known_requests_set = set(new_requests)

        # Wait before next poll
        await asyncio.sleep(poll_interval)


def setup_args(arg):
    """Set up the command-line arguments"""
    arg("-p", "--portals", help="Directory of portals")
    arg("-d", "--device", help="CUDA device to use")


if __name__ == "__main__":
    main.go(serve_requests, setup_args)
