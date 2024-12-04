#!/usr/bin/env python3-allemande

"""Generate images using the Stable Diffusion WebUI API via a1111_client"""

import os
import logging
from pathlib import Path
import yaml
from typing import AsyncIterator

from ally import main, logs, unix
import a1111_client

__version__ = "0.1.0"

logger = logs.get_logger()

prog = main.prog_info()

portals_dir = Path(os.environ["ALLEMANDE_PORTALS"]) / prog.name


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


async def process_request(portals, portal, req):
    """Process a request on a portal"""
    portal = Path(portal)
    logger.info("%s:%s - processing", portal, req)
    log_handler = None
    try:
        d = portal / "doing" / req
        os.rename(portal / "todo" / req, d)
        log_handler = logging.FileHandler(d / "log.txt")
        logger.addHandler(log_handler)

        config = yaml.safe_load(load(portals, d, "config.yaml"))
        prompt = load(portals, d, "request.txt")

        await a1111_client.a1111_client(
            output=str(d / "output"),
            prompt=prompt,
            negative_prompt=config.get("negative_prompt", ""),
            seed=config.get("seed", -1),
            sampler_name=config.get("sampler_name", "DPM++ 2M"),
            scheduler=config.get("scheduler", "Karras"),
            steps=config.get("steps", 15),
            cfg_scale=config.get("cfg_scale", 7.0),
            width=config.get("width", 1024),
            height=config.get("height", 1024),
            count=config.get("count", 1),
            adetailer=config.get("adetailer", None),
            pag=config.get("pag", False),
            hires=config.get("hires", 0.0)
        )

        os.rename(d, portal / "done" / req)
        logger.info("%s:%s - done", portal, req)
    except Exception as e:
        logger.exception("%s:%s - error: %s", portal, req, e)
        os.rename(d, portal / "error" / req)
    finally:
        if log_handler:
            logger.removeHandler(log_handler)


async def serve_requests(portals: str = str(portals_dir), poll_interval: float = 1.0):
    """Serve image generation requests from portals directory"""
    logger.info("serving requests from %s", portals)
    known_requests = set()

    for portal in Path(portals).iterdir():
        if not portal.is_dir():
            continue
        todo = portal / "todo"
        logger.info("monitoring %s", todo)

        for req in todo.iterdir():
            if not req.is_dir():
                continue
            known_requests.add((portal, req.name))
            await process_request(portals, portal, req.name)

    while True:
        new_requests = set()
        for portal in Path(portals).iterdir():
            if not portal.is_dir():
                continue
            todo = portal / "todo"

            for req in todo.iterdir():
                if not req.is_dir():
                    continue
                new_requests.add((portal, req.name))

        for portal, req_name in new_requests - known_requests:
            logger.debug("New request detected: %s in %s", req_name, portal)
            await process_request(portals, portal, req_name)

        known_requests = new_requests
        await unix.sleep(poll_interval)


def setup_args(arg):
    """Set up the command-line arguments"""
    arg("-p", "--portals", help="Directory of portals")
    arg("-i", "--poll-interval", type=float, help="Polling interval in seconds")


if __name__ == "__main__":
    main.go(serve_requests, setup_args)
