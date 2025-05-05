#!/usr/bin/env python3-allemande

"""Generate images using the Stable Diffusion WebUI API via a1111_client"""

import os
import logging
from pathlib import Path
import asyncio
import re
import math
import fcntl

import yaml

import a1111_client  # type: ignore
import slug  # type: ignore
import stamp  # type: ignore
from ally import main, logs  # type: ignore
from unprompted.unprompted_macros import parse_macros, update_macros  # type: ignore

__version__ = "0.1.1"

logger = logs.get_logger()

prog = main.prog_info()

portals_dir = Path(os.environ["ALLEMANDE_PORTALS"]) / prog.name

GPU_MUTEX = Path(os.environ["ALLEMANDE_PORTALS"]) / "gpu_mutex"

MAX_PIXELS = 1280 * 1280
MAX_HIRES_PIXELS = (1024 * 1.75) ** 2

COUNT_LIMIT = 10
STEPS_LIMIT = 150


def process_hq_macro(config: dict, sets: dict) -> dict:
    """Process hq macro and update config accordingly"""
    hq = float(sets.get("hq", 0))

    if hq == 0:
        # hq=0 - disable adetailer, no hires
        config['adetailer'] = None
        config['hires'] = 0.0
    elif hq == 1:
        # hq=1 - keep adetailer from config, no hires fix
        config['hires'] = 0.0
    else:
        # hq != 1 - set hires to hq value
        config['hires'] = hq

    return config


def limit_dimensions_and_hq(config: dict) -> dict:
    """Limit dimensions and hires to prevent excessive resource usage and bad results"""
    width = config.get("width", 768)
    height = config.get("height", 768)

    # don't allow zero or negative dimensions
    width = max(width, 1)
    height = max(height, 1)

    # lower-limit dimensions, each dimension must be at least 512
    if width < 512 or height < 512:
        min_dim = min(width, height)
        scale = 512 / min_dim
        height = math.ceil(height * scale)
        width = math.ceil(width * scale)

    # upper-limit dimensions, total pixels must be less than MAX_PIXELS
    if width * height > MAX_PIXELS:
        scale = (MAX_PIXELS / (width * height)) ** 0.5
        width = int(width * scale)
        height = int(height * scale)

    # width and height must be multiples of 64
    width = width // 64 * 64
    height = height // 64 * 64

    # limit hires fix by pixels
    hires = config.get("hires", 1.0)

    if hires and hires < 1.0:
        hires = 1.0

    if width * height * hires * hires > MAX_HIRES_PIXELS:
        hires = (MAX_HIRES_PIXELS / (width * height)) ** 0.5
        hires = round(hires - 0.005, 2)

    # update config and log
    if width != config.get("width", 1024) or height != config.get("height", 1024):
        logger.info("limiting dimensions to %dx%d", width, height)
        config['width'] = width
        config['height'] = height
    if hires != config.get("hires", 1.0):
        logger.info("limiting hires to %.2f", hires)
        config['hires'] = hires

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


def apply_shortcut(sets: dict[str, str], shape: str, quality: int):
    """Apply a shortcut to the sets macro"""
    add = {}
    add['steps'] = "15"
    add['hq'] = "0"
    if quality == 0:
        if shape == "S":
            add['width'] = "768"
            add['height'] = "768"
        elif shape == "P":
            add['width'] = "768"
            add['height'] = "1024"
        elif shape == "L":
            add['width'] = "1024"
            add['height'] = "768"
    else:
        if shape == "S":
            add['width'] = "1024"
            add['height'] = "1024"
        elif shape == "P":
            add['width'] = "960"
            add['height'] = "1280"
        elif shape == "L":
            add['width'] = "1280"
            add['height'] = "960"
        if quality == 1:
            pass
        elif quality == 2:
            add['hq'] = "1"  # use adetailer
        else:
            add['hq'] = "1.5"  # use hires-fix and adetailer (3)
        if quality == 4:
            add['steps'] = "30"
        elif quality == 5:
            add['steps'] = "45"
        elif quality == 6:
            add['steps'] = "60"
        elif quality == 7:
            add['steps'] = "90"
        elif quality == 8:
            add['steps'] = "120"
        elif quality == 9:
            add['steps'] = "150"

    sets.update({k:v for k,v in add.items() if k not in sets})


# pylint: disable=too-many-locals, too-many-branches, too-many-statements
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

        # Process macros
        macros = parse_macros(prompt)
        sets = macros.get('sets', {})
        need_update_macros = False

        # TODO for SD1.5 models limit resolution to 768x768 max, and default to 512x512?

        # Shortcuts
        for shortcut in macros:
            if re.match(r"[SPL]\d?$", shortcut):
                shape = shortcut[0]
                quality = int((shortcut+"0")[1])
                apply_shortcut(sets, shape, quality)
                need_update_macros = True
                break
        else:
            shortcut = None

        logger.debug("sets: %r", sets)

        # Process hq setting
        if 'width' in sets:
            need_update_macros = True
            config['width'] = int(sets['width'])
        if 'height' in sets:
            need_update_macros = True
            config['height'] = int(sets['height'])
        if 'hires' in sets:
            need_update_macros = True
            config['hires'] = float(sets['hires'])
        if 'seed' in sets:
            need_update_macros = True
            config['seed'] = int(sets['seed'])
        if 'pag' in sets:
            need_update_macros = True
            config['pag'] = float(sets['pag'])

        # Process rp macro (regional prompter)
        regional_kwargs = {}
        rp = macros.get("rp", {})
        if "rp" in macros:
            # change all keys to prefix rp_
            for key, value in rp.items():
                regional_kwargs[f"rp_{key}"] = value
            regional_kwargs["regional"] = regional_kwargs.pop("rp_mode", "columns")
            need_update_macros = True

        config = process_hq_macro(config, sets)
        config = limit_dimensions_and_hq(config)

        # Update settings in prompt if needed
        if need_update_macros:
            sets['width'] = str(config['width'])
            sets['height'] = str(config['height'])
            sets['hires'] = str(config['hires'])
            sets['seed'] = "---REMOVEME---"
            update = {"sets": sets, "rp": None}
            if shortcut:
                update[shortcut] = None
            prompt = update_macros(prompt, update)
            prompt = re.sub(r"seed=---REMOVEME---", "", prompt)

            # logger.info("updated prompt: %s", prompt)

        # We can update the count from the sets macro
        if 'count' in sets:
            config['count'] = int(sets['count'])

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

        # Acquire GPU mutex lock
        with GPU_MUTEX.open("w") as lockfile:
            try:
                fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX)
                # Run image gen with the lock held
                seed = await a1111_client.a1111_client(
                    output=str(d / output_stem),
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    seed=config.get("seed", -1),
                    sampler_name=config.get("sampler_name", "DPM++ 2M"),
                    scheduler=config.get("scheduler", "Karras"),
                    steps=min(config.get("steps", 15), STEPS_LIMIT),
                    cfg_scale=config.get("cfg_scale", 7.0),
                    width=config.get("width", 1024),
                    height=config.get("height", 1024),
                    count=min(config.get("count", 1), COUNT_LIMIT),
                    adetailer=config.get("adetailer", None),
                    pag=config.get("pag", 0),
                    hires=config.get("hires", 0.0),
                    pony=config.get("pony", 0.0),
                    ad_mask_k_largest=config.get("ad_mask_k_largest", 0),
                    model=config.get("model"),
                    clip_skip=config.get("clip_skip"),
                    **regional_kwargs,
                )
            finally:
                fcntl.flock(lockfile.fileno(), fcntl.LOCK_UN)

        if fmt == "jpg":
            metadata = convert_images_to_jpeg(portal, req, d)
        else:
            metadata = extract_metadata(portal, req, d)

        data = yaml.dump({
            "seed": seed,
            "metadata": metadata,
        })
        (d/"result.yaml").write_text(data, encoding="utf-8")

        os.rename(d, portal / "done" / req)
        logger.info("%s:%s - done", portal, req)
    except (Exception, KeyboardInterrupt) as e:  # pylint: disable=broad-exception-caught
        logger.exception("%s:%s - error: %s", portal, req, e)
        os.rename(d, portal / "error" / req)
    finally:
        if log_handler:
            logger.removeHandler(log_handler)


def convert_images_to_jpeg(portal: Path, req: str, d: Path, quality: int = 95):
    """Convert all images in a directory to JPEG, deleting the original PNGs and preserving metadata"""
    metadata = {}
    for img in d.iterdir():
        if img.suffix.lower() == ".png":
            dest = img.with_suffix(".jpg")
            try:
                metadata[img.stem] = stamp.convert_image(img, dest, quality=quality)
                img.unlink()
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.exception("%s:%s - error converting images to JPEG: %s", portal, req, e)
                dest.unlink()
                # continue with PNG
                # TODO ideally stamp would clean up
    return metadata


def extract_metadata(portal: Path, req: str, d: Path):
    """Extract metadata from all images in a directory"""
    metadata = {}
    for img in d.iterdir():
        try:
            metadata[img.name] = stamp.extract_metadata(img)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("%s:%s - error extracting metadata: %s", portal, req, e)
    return metadata


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
