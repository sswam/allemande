#!/usr/bin/env python3-allemande

"""Generate images using the Stable Diffusion WebUI API via a1111_client"""

import os
import logging
from pathlib import Path
import asyncio
import re

import yaml

import a1111_client  # type: ignore
import slug  # type: ignore
import stamp  # type: ignore
from ally import main, logs
from unprompted.unprompted_macros import parse_macros

__version__ = "0.1.1"

logger = logs.get_logger()

prog = main.prog_info()

portals_dir = Path(os.environ["ALLEMANDE_PORTALS"]) / prog.name


def process_hq_macro(prompt: str, config: dict) -> dict:
    """Process hq macro in prompt and update config accordingly"""
    macros = parse_macros(prompt)

    sets = macros.get('sets', {})
    hq = float(sets.get('hq', 0))

    if hq == 0:
        # hq not set - disable adetailer, no hires
        config['adetailer'] = None
        config['hires'] = 0.0
    elif hq == 1:
        # hq=1 - keep adetailer from config, no hires
        config['hires'] = 0.0
    else:
        # hq != 1 - set hires to hq value
        config['hires'] = hq

    return config


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


async def process_request(portals: str, portal_str: Path, req: str):
    """Process a request on a portal"""
    portal = Path(portal_str)
    logger.info("%s:%s - processing", portal, req)
    log_handler = None
    seed = None

    try:
        d = portal / "doing" / req
        os.rename(portal / "todo" / req, d)
        log_handler = logging.FileHandler(d / "log.txt")
        logger.addHandler(log_handler)

        config = yaml.safe_load(load(portals, d, "config.yaml"))
        prompt = load(portals, d, "request.txt")

        # Process hq macro
        config = process_hq_macro(prompt, config)

        output_stem = slug.slug(prompt)[:70]

        negative_prompt = config.get("negative_prompt", "")

        if negative_prompt == "":
            try:
                prompt, negative_prompt = re.split(r"\s+NEGATIVE\s+", prompt, 1)
            except ValueError:
                pass

        fmt = config.get("format", "jpg")
        if fmt not in ("jpg", "png"):
            raise ValueError(f"unknown format: {fmt}")

        seed = await a1111_client.a1111_client(
            output=str(d / output_stem),
            prompt=prompt,
            negative_prompt=negative_prompt,
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
            hires=config.get("hires", 0.0),
            pony=config.get("pony", 0.0),
            ad_mask_k_largest=config.get("ad_mask_k_largest", 0),
            model=config.get("model"),
        )

        if fmt == "jpg":
            convert_images_to_jpeg(portal, req, d)

        data = yaml.dump({"seed": seed})
        (d/"result.yaml").write_text(data, encoding="utf-8")

        os.rename(d, portal / "done" / req)
        logger.info("%s:%s - done", portal, req)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.exception("%s:%s - error: %s", portal, req, e)
        os.rename(d, portal / "error" / req)
    finally:
        if log_handler:
            logger.removeHandler(log_handler)


def convert_images_to_jpeg(portal: Path, req: str, d: Path, quality: int = 95):
    """Convert all images in a directory to JPEG, deleting the original PNGs and preserving metadata"""
    for img in d.iterdir():
        if img.suffix.lower() == ".png":
            dest = img.with_suffix(".jpg")
            try:
                stamp.convert_image(img, dest, quality=quality)
                img.unlink()
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.exception("%s:%s - error converting images to JPEG: %s", portal, req, e)
                dest.unlink()
                # continue with PNG
                # TODO ideally stamp would clean up


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


async def serve_requests(portals: str = str(portals_dir), poll_interval: float = 0.1):
    """Serve image generation requests from portals directory"""
    logger.info("serving requests from %s", portals)
    known_requests = find_todo_requests(portals)
    for portal, req in known_requests:
        logger.debug("Initial request detected: %s in %s", req, portal)
        await process_request(portals, portal, req)

    known_requests_set = set(known_requests)

    while True:
        new_requests = find_todo_requests(portals)
        for portal, req_name in new_requests:
            if (portal, req_name) in known_requests_set:
                continue
            logger.debug("New request detected: %s in %s", req_name, portal)
            await process_request(portals, portal, req_name)

        known_requests_set = set(new_requests)

        # Wait before next poll
        await asyncio.sleep(poll_interval)


def setup_args(arg):
    """Set up the command-line arguments"""
    arg("-p", "--portals", help="Directory of portals")
    arg("-i", "--poll-interval", type=float, help="Polling interval in seconds")


if __name__ == "__main__":
    main.go(serve_requests, setup_args)
