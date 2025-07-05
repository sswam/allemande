#!/usr/bin/env python3-allemande

"""Generate images using the Stable Diffusion WebUI API via a1111_client"""

import os
import logging
from pathlib import Path
import asyncio
import re
import math
import fcntl
import random
from dataclasses import dataclass
from typing import Any
import time

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

# TODO: other ideas for limits
# - MAX_COUNT depends on number of steps, etc
# - an actual time limit, just stop after that time
# - fair queueing, handle multiple requests. How? need to know user?

MAX_COUNT = 10
MAX_STEPS = 30  # 150

JOB_PENALTY = 0.01  # Adds about 1/10 second per medium sized job
JOB_BASE_TIME = 25 # seconds, base time for a job at 1024x1024x15
MIN_STEPS = 15
MIN_JOB_PENALTY = 1
MAX_JOB_PENALTY = 2
MAX_JOB_DELAY = 420  # 7 minutes, after that the client might timeout
ADETAILER_TIME = 3  # seconds, how long adetailer takes to run roughly


def process_hq_macro(config: dict, sets: dict) -> dict:
    """Process hq macro and update config accordingly"""
    hq = float(sets.get("hq", 0))

    if hq == 0:
        # hq=0 - disable adetailer, no hires
        config["adetailer"] = None
        config["hires"] = 0.0
    elif hq == 1:
        # hq=1 - keep adetailer from config, no hires fix
        config["hires"] = 0.0
    else:
        # hq != 1 - set hires to hq value
        config["hires"] = hq

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
        config["width"] = width
        config["height"] = height
    if hires != config.get("hires", 1.0):
        logger.info("limiting hires to %.2f", hires)
        config["hires"] = hires

    # limit steps to MAX_STEPS
    if config.get("steps", 15) > MAX_STEPS:
        logger.info("limiting steps to %d", MAX_STEPS)
        config["steps"] = MAX_STEPS

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
    add["steps"] = "15"
    add["hq"] = "0"
    if quality == 0:
        if shape == "S":
            add["width"] = "768"
            add["height"] = "768"
        elif shape == "P":
            add["width"] = "768"
            add["height"] = "1024"
        elif shape == "L":
            add["width"] = "1024"
            add["height"] = "768"
        elif shape == "T":
            add["width"] = "640"
            add["height"] = "1120"
        elif shape == "W":
            add["width"] = "1120"
            add["height"] = "640"
    else:
        if shape == "S":
            add["width"] = "1024"
            add["height"] = "1024"
        elif shape == "P":
            add["width"] = "960"
            add["height"] = "1280"
        elif shape == "L":
            add["width"] = "1280"
            add["height"] = "960"
        elif shape == "T":
            add["width"] = "768"
            add["height"] = "1344"
        elif shape == "W":
            add["width"] = "1344"
            add["height"] = "768"
        if quality == 1:
            pass
        elif quality == 2:
            add["hq"] = "1"  # use adetailer
        else:
            add["hq"] = "1.5"  # use hires-fix and adetailer (3)
        if quality == 4:
            add["steps"] = "30"
        elif quality == 5:
            add["steps"] = "45"
        elif quality == 6:
            add["steps"] = "60"
        elif quality == 7:
            add["steps"] = "90"
        elif quality == 8:
            add["steps"] = "120"
        elif quality == 9:
            add["steps"] = "150"

    sets.update({k: v for k, v in add.items() if k not in sets})


# Global priority queue
image_queue = asyncio.PriorityQueue()


# User jobs count
user_usage: dict[str, int] = {}


@dataclass(order=True)
class ImageJob:
    priority: int
    d: Path
    output_stem: str
    prompt: str
    negative_prompt: str
    seed: int
    config: dict[str, Any]
    regional_kwargs: dict[str, Any]
    i: int
    count: int
    portal: Path
    request_time: float
    duration: float


job = None


async def process_image_queue():
    """Process jobs from the image queue"""
    global job  # pylint: disable=global-statement
    while True:
        try:
            # Log the queue with priority and user-name
            logger.info("Queue size: %d", image_queue.qsize())
            current_time = time.time()
            for job in sorted(list(image_queue._queue), key=lambda j: j.priority):
                logger.info("Job: %.0f: %s", job.priority - current_time, job.config.get("user"))

            # Get job from queue
            job = await image_queue.get()

            start_time = time.time()
            logger.info("\nRunning Job: %.0f: %s", job.priority - start_time, job.config.get("user"))

            if start_time - job.request_time > MAX_JOB_DELAY:
                # Don't process the job if it has been in the queue for too long, as the client will have timed out
                await complete_batch(job)
            else:
                # Process the job
                with GPU_MUTEX.open("w") as lockfile:
                    try:
                        fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX)
                        await a1111_client.a1111_client(
                            output=str(job.d / f"{job.output_stem}_{job.seed}"),
                            prompt=job.prompt,
                            negative_prompt=job.negative_prompt,
                            seed=job.seed,
                            sampler_name=job.config.get("sampler_name", "DPM++ 2M"),
                            scheduler=job.config.get("scheduler", "Karras"),
                            steps=min(job.config.get("steps", 15), MAX_STEPS),
                            cfg_scale=job.config.get("cfg_scale", 7.0),
                            width=job.config.get("width", 1024),
                            height=job.config.get("height", 1024),
                            count=1,
                            adetailer=job.config.get("adetailer", None),
                            ad_checkpoint=job.config.get("ad_checkpoint", None),
                            pag=job.config.get("pag", 0),
                            hires=job.config.get("hires", 0.0),
                            pony=job.config.get("pony", 0.0),
                            ad_mask_k_largest=job.config.get("ad_mask_k_largest", 0),
                            model=job.config.get("model"),
                            clip_skip=job.config.get("clip_skip"),
                            **job.regional_kwargs,
                        )
                    finally:
                        fcntl.flock(lockfile.fileno(), fcntl.LOCK_UN)

                    # Check if this is the last job in the batch
                    if job.i == job.count - 1:
                        await complete_batch(job)
                end_time = time.time()
                logger.info("Job duration vs estimate: %.2f seconds vs %.2f", end_time - start_time, job.duration)
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"Error processing image job: {e}")
            # Mark task as done even if it failed
        finally:
            job = None
            image_queue.task_done()


async def complete_batch(job: ImageJob):
    portal = job.portal
    fmt = job.config.get("format", "jpg")
    req = job.d.name
    if fmt == "jpg":
        metadata = convert_images_to_jpeg(portal, req, job.d)
    else:
        metadata = extract_metadata(portal, req, job.d)

    data = yaml.dump(
        {
            "seed": job.seed,
            "metadata": metadata,
        }
    )
    (job.d / "result.yaml").write_text(data, encoding="utf-8")

    os.rename(job.d, portal / "done" / req)
    logger.info("%s:%s - done", portal, req)


def estimate_job_weight(job: dict[str, Any]) -> float:
    """Estimate the weight of a job compared to the base job"""
    job_weight = 1.0

    log = logger.debug

    log("job_weight 1: %.2f", job_weight)

    config = job.config

    # multiply based on steps
    steps = config.get("steps", MIN_STEPS)
    job_weight *= config.get("steps", MIN_STEPS) / MIN_STEPS
    log("Steps weight: %.2f", config.get("steps", MIN_STEPS) / MIN_STEPS)

    log("job_weight 2: %.2f", job_weight)

    # multiply based on image size, relative to 1024x1024
    job_weight *= config.get("width", 1024) * config.get("height", 1024) / (1024 * 1024)
    log("Image size weight: %.2f", config.get("width", 1024) * config.get("height", 1024) / (1024 * 1024))

    log("job_weight 3: %.2f", job_weight)

    # add for hires
    job_weight += job_weight * (config.get("hires") or 1.0) ** 2 * 0.3
    log("Hires weight: %.2f", (config.get("hires") or 1.0) ** 2)

    log("job_weight 4: %.2f", job_weight)

    # add for adetailer
    job_weight += len(config.get("adetailer") or []) * ADETAILER_TIME / JOB_BASE_TIME
    log("Adetailer weight: %.2f", len(config.get("adetailer") or []) * ADETAILER_TIME / JOB_BASE_TIME)

    log("job_weight 5: %.2f", job_weight)

    # multiply by 1.5 if using regional prompter
    if job.regional_kwargs:
        log("Regional prompter detected, increasing job weight")
        job_weight *= 1.5

    log("Estimated job weight: %.2f", job_weight)

    return job_weight


def get_user_job_penalty(usage: float) -> float:
    """
    Calculate the job penalty for a user based on the number of jobs they have run.
    Soft max between MIN_JOB_PENALTY and MAX_JOB_PENALTY.
    """
    return MIN_JOB_PENALTY + (MAX_JOB_PENALTY - MIN_JOB_PENALTY) * (
        1 - 1 / (usage * JOB_PENALTY / (MAX_JOB_PENALTY - MIN_JOB_PENALTY) + 1)
    )


async def enqueue_image_jobs(
    d: Path, prompt: str, negative_prompt: str, output_stem: str, config: dict, regional_kwargs: dict, portal: Path
) -> int:
    """Enqueue image generation jobs into the priority queue"""
    seed = config.get("seed", random.randint(0, 2**32 - 1))
    count = min(config.get("count", 1), MAX_COUNT)

    user = config.get("user", None)

    current_time = time.time()

    # TODO can estimate job duration / weight better from parameters
    # TODO or measure job duration

    # penalty = min(JOB_PENALTY * jobs_count, MAX_PENALTY)

    # penalty = MAX_PENALTY * (1 - 1/(jobs_count * JOB_PENALTY / MAX_PENALTY + 1))

    logger.info("Enqueuing %d jobs for user %s", count, user)

    # Calculate the priority for the first job, considering existing queued jobs for the user
    priority = current_time
    for j in list(image_queue._queue) + [job]:
        if not j or j.config.get("user") != user:
            continue
        priority += j.duration
    logger.info("priority: %.2f", priority - current_time)

    # Enqueue each image job
    for i in range(count):
        # logger.info("enqueuing job %d/%d for user %s with jobs count %s", i + 1, count, user, user_usage.get(user, 0))
        new_job = ImageJob(
            priority=priority,
            d=d,
            output_stem=output_stem,
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=seed + i,
            config=config,
            regional_kwargs=regional_kwargs,
            i=i,
            count=count,
            portal=portal,
            request_time=current_time,
            duration=0,
        )
        weight = estimate_job_weight(new_job)
        job_penalty = get_user_job_penalty(user_usage.get(user, 0.0))
        new_job.duration = weight * job_penalty * JOB_BASE_TIME
        logger.info("weight, job_penalty, duration: %.2f, %.2f, %.2f", weight, job_penalty, new_job.duration)
        await image_queue.put(new_job)
        priority += new_job.duration
        user_usage[user] = user_usage.get(user, 0) + weight

    return seed


def process_prompt_and_config(prompt: str, config: dict, macros: dict) -> tuple[str, str, dict, dict, bool, dict[str, str], str]:
    """Process prompt and config, returning updated values and whether macros need updating"""
    sets = macros.get("sets", {})
    need_update_macros = False
    regional_kwargs = {}

    # Process shortcuts
    for shortcut in macros:
        if re.match(r"[SPLTW]\d?$", shortcut):
            shape = shortcut[0]
            quality = int((shortcut + "0")[1])
            apply_shortcut(sets, shape, quality)
            need_update_macros = True
            break
    else:
        shortcut = None

    # Process settings
    for setting in ["steps", "width", "height", "hires", "seed", "pag", "ad_checkpoint"]:
        if setting not in sets:
            continue
        value = sets[setting]
        need_update_macros = True
        if setting in ["steps", "width", "height", "seed"]:
            config[setting] = int(value)
        elif setting in ["ad_checkpoint"]:
            config[setting] = value
        else:
            config[setting] = float(value)

    # Process regional prompter
    rp = macros.get("rp", {})
    if "rp" in macros:
        # change all keys to prefix rp_
        for key, value in rp.items():
            regional_kwargs[f"rp_{key}"] = value
        regional_kwargs["regional"] = regional_kwargs.pop("rp_mode", "columns")
        need_update_macros = True

    config = process_hq_macro(config, sets)
    config = limit_dimensions_and_hq(config)

    # Process negative prompt
    negative_prompt = config.get("negative_prompt", "")
    if negative_prompt == "":
        try:
            prompt, negative_prompt = re.split(r"\s+NEGATIVE\s+", prompt, 1)
        except ValueError:
            pass

    # We can update the count from the sets macro
    if "count" in sets:
        config["count"] = int(sets["count"])

    return prompt, negative_prompt, config, regional_kwargs, need_update_macros, sets, shortcut


def update_prompt_with_macros(prompt: str, config: dict, sets: dict[str, str], shortcut: str = None) -> str:
    """Update the prompt with macros"""
    sets["width"] = str(config["width"])
    sets["height"] = str(config["height"])
    sets["hires"] = str(config["hires"])
    sets["steps"] = str(config["steps"])
    for k in ["seed", "pag", "ad_checkpoint"]:
        if k in sets:
            sets[k] = "---REMOVEME---"
    update = {"sets": sets, "rp": None}
    logger.info("update_prompt_with_macros: sets=%s", sets)
    if shortcut:
        update[shortcut] = None
    prompt = update_macros(prompt, update)
    prompt = re.sub(r"\w+=---REMOVEME---", "", prompt)
    return prompt


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
        prompt, negative_prompt, config, regional_kwargs, need_update_macros, sets, shortcut = process_prompt_and_config(
            prompt, config, macros
        )

        if need_update_macros:
            prompt = update_prompt_with_macros(prompt, config, sets)

        output_stem = slug.slug(prompt)[:70]

        fmt = config.get("format", "jpg")
        if fmt not in ("jpg", "png"):
            raise ValueError(f"unknown format: {fmt}")

        seed = await enqueue_image_jobs(d, prompt, negative_prompt, output_stem, config, regional_kwargs, portal)
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

    queue_processor = asyncio.create_task(process_image_queue())

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
