#!/usr/bin/env python3-allemande

"""Generate images using the Stable Diffusion WebUI API via forge_client"""

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
import bisect

import yaml

import forge_client  # type: ignore
import slug  # type: ignore
import stamp  # type: ignore
from ally import main, logs  # type: ignore
from unprompted_macros import parse_macros, update_macros  # type: ignore
from ally.util import clamp, read_lines_from_file

__version__ = "0.2.2"

logger = logs.get_logger()

prog = main.prog_info()

home_dir = Path(os.environ["ALLEMANDE_HOME"])
portals_dir = Path(os.environ["ALLEMANDE_PORTALS"]) / "image_a1111"  # FIXME prog.name

GPU_MUTEX = Path(os.environ["ALLEMANDE_PORTALS"]) / "gpu_mutex"

MAX_PIXELS = 1280 * 1280
# MAX_HIRES_PIXELS = (1024 * 1.75) ** 2
MAX_HIRES_PIXELS = (1024 * 2.8125) ** 2

# TODO: other ideas for limits
# - MAX_COUNT depends on number of steps, etc
# - an actual time limit, just stop after that time
# - fair queueing, handle multiple requests. How? need to know user?

DEFAULT_SHORTCUT = "P0"
MAX_COUNT = 10
MAX_STEPS = 150  # 30

JOB_PENALTY = 0.01  # Adds about 1/10 second per medium sized job
JOB_BASE_TIME = 25 # 120 # 60 # 25 # seconds, base time for a job at 1024x1024x15
JOB_BASE_TIME_PRIVATE = 75 # 120 # 60 # 25 # seconds, base time for a job at 1024x1024x15
MIN_STEPS = 15
MIN_JOB_PENALTY = 1
MAX_JOB_PENALTY = 2
MAX_JOB_DELAY = 1020  # 17 minutes, after that the client might timeout
MAX_QUEUE_DELAY = 4800  # 80 minutes, don't schedule extra jobs beyond that point
ADETAILER_TIME = 3  # seconds, how long adetailer takes to run roughly

# Hacky support for special occasions!  i.e. Halloween
SPECIAL_OCCASION_ENABLE = False
SPECIAL_OCCASION_PROMPT = """[opt 80 0.8 1.7] corpse, [/opt], [opt 80 0.8 1.7] horror, [/opt] [opt 80 0.8 1.7] gore, [/opt], [opt 80 0.8 1.7] blood, [/opt]
[opt 70 0.8 1.8] dead, decay, [/opt]
[set n] [random _min=1 _max=3] [/set]
[opt 100 1.2 1.9] monster, [choose n] zombie | werewolf | furry, body fur | monster girl | vampire | mummy, bandages, bandaged arm, bandaged leg, bandage over one eye | ghost | oni | demon, demon girl, demon wings horns | angel, angel wings | goblin | chimera | dragon girl | mermaid [/choose] [/opt],
[opt 50]glowing eyes[/opt], [opt 70]g1g3r[/opt], twisted limbs, grotesque features, ghostly
"""
SPECIAL_OCCASION_LORAS = "<lora:g1g3r:0.8> <lora:scifi-horror-000006:0.8>"
# SPECIAL_OCCASION_PROMPT = "(corpse, zombie, horror, gore:1.5), (dead, decay, zombie: 1.9), glowing eyes, g1g3r, twisted limbs, grotesque features, ghostly"
# SPECIAL_OCCASION_LORAS = "<lora:g1g3r:1> <lora:scifi-horror-000006:1>"
SPECIAL_OCCASION_EXCEPTION_PREFIXES = []  # TODO from file

# TODO: load from server or receive the user's priority with each request
USER_PRIORITY_NORMAL = 0, 1   # absolute offset, multiplier
USER_PRIORITY_NOW = -1000, 0
USERS_VIP = read_lines_from_file(home_dir/"users_vip.txt")
USERS_SUPPORTER = read_lines_from_file(home_dir/"users_supporter.txt")
USER_PRIORITY = {
    user: USER_PRIORITY_NOW for user in USERS_VIP
}

USER_ALLOW_PRIVATE = set(USERS_SUPPORTER + USERS_VIP)
ALLOW_PRIVATE_ALL = True

SHAPE_GEOMETRY = {
    "E": (("512", "512"), ("640", "640")),
    "S": (("768", "768"), ("1024", "1024")),
    "p": (("768", "896"), ("896", "1152")),
    "P": (("768", "1024"), ("960", "1280")),
    "l": (("896", "768"), ("1152", "896")),
    "L": (("1024", "768"), ("1280", "960")),
    "t": (("640", "896"), ("832", "1216")),
    "T": (("640", "1120"), ("768", "1344")),
    "w": (("896", "640"), ("1216", "832")),
    "W": (("1120", "640"), ("1344", "768")),
    "v": (("640", "1280"), ("768", "1536")),
    "V": (("512", "1280"), ("640", "1536")),
    "x": (("1280", "640"), ("1536", "768")),
    "X": (("1280", "512"), ("1536", "640"))
}

QUALITY_STEPS = {
    4: "30",
    5: "45",
    6: "60",
    7: "90",
    8: "120",
    9: "150"
}

QUALITY_HQ = {
    0: 0,
    2: 1,
    3: 1.5,
    4: 2,
    5: 3,   # 2.86 2.8125  >4K height
}


def lookup_hq(value):
    """
    Look up hq value from QUALITY_HQ dict.
    Finds the greatest key <= the lookup value and returns that value.
    """
    keys = sorted(QUALITY_HQ.keys())
    # bisect_right gives us the insertion point, subtract 1 for greatest key <=
    idx = bisect.bisect_right(keys, value) - 1
    return QUALITY_HQ[keys[idx]]


QUALITY_MIN = 0
QUALITY_MAX = 9   # TODO drop to 4 again if it's a problem! secret feature...


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

    resolution_option = 0 if quality == 0 else 1
    add["width"], add["height"] = SHAPE_GEOMETRY[shape][resolution_option]

    # add["hq"] = "0"
    # if quality == 2:
    #     add["hq"] = "1"  # use adetailer
    # elif quality == 3:
    #     add["hq"] = "1.5"  # use hires-fix and adetailer (3)
    # elif quality == 4:
    #     add["hq"] = "1.5"  # use hires-fix and adetailer (3)
    # elif quality == 5:
    #     add["hq"] = "2"  # use hires-fix and adetailer (3)

    add["hq"] = str(lookup_hq(quality))

    add["steps"] = QUALITY_STEPS.get(quality, "15")

    logger.info("HQ: quality=%s hq=%s steps=%s", quality, add["hq"], add["steps"])

    sets.update({k: v for k, v in add.items() if k not in sets})


# User jobs count
user_usage: dict[str, float] = {}

# Day crossover detection
day_start = None

@dataclass(order=True)
class ImageJob:
    """Represents a single image generation job with priority scheduling"""
    priority: float  # Changed to float since we're using timestamps
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


# Global priority queue
image_queue: asyncio.PriorityQueue[ImageJob] = asyncio.PriorityQueue()


job: ImageJob | None = None


def get_queue_jobs() -> list[ImageJob]:
    """Get list of jobs from queue, for inspection only"""

    return list(image_queue._queue)  # pylint: disable=protected-access  # type: ignore[missing-attribute]


def get_sorted_queue_jobs() -> list[ImageJob]:
    """Get sorted list of jobs from queue, for inspection only"""
    return sorted(get_queue_jobs(), key=lambda j: j.priority)


def ensure_queue_not_in_past(current_time: float):
    """Ensure that the queue does not contain jobs scheduled in the past"""
    global image_queue
    queue_jobs = get_sorted_queue_jobs()

    set_time = current_time
    changed = False
    for job in queue_jobs:
        if job.priority >= set_time:
            break
        job.priority = set_time
        set_time += 0.001  # ensure unique priority and maintain order
        changed = True

    if changed:
        new_queue = asyncio.PriorityQueue()
        for job in queue_jobs:
            new_queue.put_nowait(job)
        image_queue = new_queue


def find_source_image(d: Path) -> Path | None:
    """Find a source image file (source.*) in the directory for img2img"""
    for pattern in ["source.*"]:
        matches = list(d.glob(pattern))
        if matches:
            return matches[0]
    return None


async def process_image_queue():
    """Process jobs from the image queue"""
    global job  # pylint: disable=global-statement
    while True:
        try:
            # Log the queue with priority and user-name
            logger.info("Queue size: %d", image_queue.qsize())
            current_time = time.time()
            ensure_queue_not_in_past(current_time)
            queue_jobs = get_sorted_queue_jobs()
            for job in queue_jobs:
                logger.info("Job: %.0f: %s", job.priority - current_time, job.config.get("user"))

            # Get job from queue
            job = await image_queue.get()

            start_time = time.time()
            logger.info("\nRunning Job: %.0f: %s", job.priority - start_time, job.config.get("user"))

            if start_time - job.request_time > MAX_JOB_DELAY:
                # Don't process the job if it has been in the queue for too long, as the client will have timed out
                logger.info("skipping old job: %.0f seconds old, more than %.0f seconds", start_time - job.request_time, MAX_JOB_DELAY)
                await complete_batch(job)
            else:
                # Process the job
                with GPU_MUTEX.open("w") as lockfile:
                    try:
                        fcntl.flock(lockfile.fileno(), fcntl.LOCK_EX)

                        # Check for img2img mode
                        source_image = find_source_image(job.d)
                        img2img_kwargs = {}
                        if source_image:
                            logger.info("img2img mode detected with source image: %s", source_image)
                            # TODO: Placeholder - need to pass image data to forge_client
                            # img2img_kwargs["init_images"] = [...]
                            # img2img_kwargs["denoising_strength"] = job.config.get("denoising_strength", 0.75)
                            img2img_kwargs["img2img_mode"] = True
                            img2img_kwargs["source_image_path"] = str(source_image)

                        await forge_client.request(
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
                            model=job.config.get("model", None),
                            clip_skip=job.config.get("clip_skip"),
                            **img2img_kwargs,
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


def estimate_job_weight(job: ImageJob) -> float:
    """Estimate the weight of a job compared to the base job"""
    job_weight = 1.0

    log = logger.debug

    log("job_weight 1: %.2f", job_weight)

    config = job.config

    # multiply based on steps
    steps = config.get("steps", MIN_STEPS)
    job_weight *= steps / MIN_STEPS

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
    global day_start
    seed = config.get("seed", random.randint(0, 2**32 - 1))
    count = min(config.get("count", 1), MAX_COUNT)

    user = config.get("user", None)
    room = config.get("room", None)

    is_private = user and room and room.startswith(f"{user}/")

    if is_private and not (ALLOW_PRIVATE_ALL or user in USER_ALLOW_PRIVATE):
        raise PermissionError(f"User {user} is not currently allowed to use image gen in a private room: {room}; please speak to Sam for options")

    job_base_time = JOB_BASE_TIME_PRIVATE if is_private else JOB_BASE_TIME

    current_time = time.time()

    # Reset usage for all users every 24 hours
    if day_start is None or current_time - day_start > 24 * 3600:
        day_start = current_time
        user_usage.clear()

    # TODO can estimate job duration / weight better from parameters
    # TODO or measure job duration

    # penalty = min(JOB_PENALTY * jobs_count, MAX_PENALTY)

    # penalty = MAX_PENALTY * (1 - 1/(jobs_count * JOB_PENALTY / MAX_PENALTY + 1))

    logger.info("Enqueuing %d jobs for user %s", count, user)

    # Calculate the priority for the first job, considering existing queued jobs for the user
    priority = current_time
    for j in get_queue_jobs() + ([] if job is None else [job]):
        if not j or j.config.get("user") != user:
            continue
        priority += j.duration
    logger.info("priority: %.2f", priority - current_time)

    # user priority adjustment
    if user in USER_PRIORITY:
        user_offset, user_multiplier = USER_PRIORITY[user]
        user_offset_sign = "-" if user_offset < 0 else "+"
        logger.info("user priority: %s: * %.2f %s %d", user, user_multiplier, user_offset_sign, abs(user_offset))
    else:
        user_offset, user_multiplier = USER_PRIORITY_NORMAL

    # Enqueue each image job
    for i in range(count):
        # logger.info("enqueuing job %d/%d for user %s with jobs count %s", i + 1, count, user, user_usage.get(user, 0))

        priority_adjusted = user_multiplier * priority + user_offset

        new_job = ImageJob(
            priority = priority_adjusted,
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
        job_penalty = 0 if not user else get_user_job_penalty(user_usage.get(user, 0.0))
        duration = weight * job_penalty * job_base_time
        duration_adjusted = duration * user_multiplier
        new_job.duration = duration_adjusted
        logger.info("weight, job_penalty, duration: %.2f, %.2f, %.2f", weight, job_penalty, new_job.duration)

        if priority_adjusted - current_time > MAX_QUEUE_DELAY:
            # Don't add the job if would run too far out in the future, as the client will have timed out, and better to give immediate feedback for too many pokes, and not clutter the queue
            logger.info("skipping new job: priority %.0f > %.0f seconds", priority_adjusted, MAX_QUEUE_DELAY)
            await complete_batch(new_job)
            break
        await image_queue.put(new_job)
        priority += new_job.duration
        if user:
            user_usage[user] = user_usage.get(user, 0.0) + weight

    return seed


def process_prompt_and_config(prompt: str, config: dict, macros: dict, room: str|None) -> tuple[str, str, dict, dict, bool, dict[str, str], str | None]:
    """Process prompt and config, returning updated values and whether macros need updating"""
    room = room or ""
    sets = macros.get("sets", {})
    need_update_macros = False
    regional_kwargs = {}

    # Process shortcuts
    for macro_key in macros:
        if re.match(r"[SpPlLtTwWvVxX]\d?$", macro_key):
            shortcut = macro_key # Assign the found shortcut
            break
    else:
        shortcut = DEFAULT_SHORTCUT
    if len(shortcut) == 1:
        shortcut += DEFAULT_SHORTCUT[1]

    shape = shortcut[0]
    quality = int((shortcut)[1])

    quality = clamp(quality, QUALITY_MIN, QUALITY_MAX)

    apply_shortcut(sets, shape, quality)
    need_update_macros = True

    # Process settings
    for setting in ["steps", "width", "height", "hires", "seed", "pag", "ad_checkpoint", "denoising_strength"]:
        if setting not in sets:
            continue
        value = sets.pop(setting)
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

    if SPECIAL_OCCASION_ENABLE and not any(room.startswith(prefix) for prefix in SPECIAL_OCCASION_EXCEPTION_PREFIXES):
        if "rp" in macros and "ADDCOMM" in prompt:
            prompt = prompt.replace("ADDCOMM", f" {SPECIAL_OCCASION_PROMPT} ADDCOMM {SPECIAL_OCCASION_LORAS} ")
        else:
            prompt += f" BREAK {SPECIAL_OCCASION_PROMPT} {SPECIAL_OCCASION_LORAS}"
        logger.info("special occasion, new prompt: %s", prompt)

    return prompt, negative_prompt, config, regional_kwargs, need_update_macros, sets, shortcut


def update_prompt_with_macros(prompt: str, config: dict, sets: dict[str, str], shortcut: str | None = None) -> str:
    """Update the prompt with macros"""
    sets["width"] = str(config["width"])
    sets["height"] = str(config["height"])
    sets["hires"] = str(config["hires"])
    sets["steps"] = str(config["steps"])
    # Remove settings that shouldn't be in the final prompt sets string
    for k in ["seed", "pag", "ad_checkpoint", "denoising_strength"]:
        if k in sets:
            sets[k] = "---REMOVEME---"
    update = {"sets": sets, "rp": None}
    logger.info("update_prompt_with_macros: sets=%s, shortcut=%s", sets, shortcut)
    if shortcut:
        update[shortcut] = None
    prompt = update_macros(prompt, update)
    prompt = re.sub(r"\w+=---REMOVEME---", "", prompt)
    return prompt


async def process_request(portals: str, portal_str: Path, req: str) -> None:
    """Process a request on a portal"""
    portal = Path(portal_str)
    logger.info("%s:%s - processing", portal, req)
    log_handler = None
    seed = None

    d = None

    try:
        d = portal / "doing" / req
        try:
            os.rename(portal / "todo" / req, d)
        except OSError as e:
            logger.warning("%s:%s - failed to rename from todo to doing, possibly handled by another process: %s", portal, req, e)
            return

        log_handler = logging.FileHandler(d / "log.txt")
        logger.addHandler(log_handler)

        config = yaml.safe_load(load(portals, d, "config.yaml"))
        prompt = load(portals, d, "request.txt")

        room = config.get("room", None)

        # Process macros
        macros = parse_macros(prompt)
        prompt, negative_prompt, config, regional_kwargs, need_update_macros, sets, shortcut = process_prompt_and_config(
            prompt, config, macros, room
        )

        if need_update_macros:
            prompt = update_prompt_with_macros(prompt, config, sets, shortcut)

        slugged_prompt = slug.slug(prompt)
        if isinstance(slugged_prompt, list):
            output_stem = "-".join(slugged_prompt)[:70]
        elif slugged_prompt:
            output_stem = slugged_prompt[:70]
        else:
            output_stem = "image"

        fmt = config.get("format", "jpg")
        if fmt not in ("jpg", "png"):
            raise ValueError(f"unknown format: {fmt}")

        seed = await enqueue_image_jobs(d, prompt, negative_prompt, output_stem, config, regional_kwargs, portal)

        logger.debug("seed is not used!  %s", seed)
    except (Exception, PermissionError, KeyboardInterrupt) as e:  # pylint: disable=broad-exception-caught
        logger.exception("%s:%s - error: %s", portal, req, e)
        if d:
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
                if dest.exists():
                    dest.unlink()
                # The original PNG remains, which is better than losing the image entirely.
                # TODO ideally stamp would clean up
    return metadata


def extract_metadata(portal: Path, req: str, d: Path):
    """Extract metadata from all images in a directory"""
    metadata = {}
    for img in d.iterdir():
        # Only process image files (png, jpg, jpeg)
        if img.suffix.lower() not in (".png", ".jpg", ".jpeg"):
            continue
        try:
            metadata[img.name] = stamp.extract_metadata(img)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.exception("%s:%s - error extracting metadata from %s: %s", portal, req, img.name, e)
    return metadata


def find_todo_requests(portals: str = str(portals_dir)) -> list[tuple[Path, str]]:
    """Find all requests in the todo directories"""
    requests = []
    portals_root = Path(portals)
    if not portals_root.exists():
        logger.error("Portals directory not found: %s", portals)
        return requests
    if not portals_root.is_dir():
        logger.error("Portals path is not a directory: %s", portals)
        return requests

    for portal in portals_root.iterdir():
        if not portal.is_dir():
            continue
        todo = portal / "todo"
        if not todo.is_dir():
            logger.warning("Skipping portal %s, no todo directory found", portal)
            continue

        for req in todo.iterdir():
            if not req.is_dir():
                continue
            # Check for required files to consider it a valid request directory
            if (req / "request.txt").exists() and (req / "config.yaml").exists():
                requests.append((portal, req.name))
            else:
                logger.warning("Skipping incomplete request directory: %s (missing request.txt or config.yaml)", req)

    requests.sort(key=lambda x: (x[0].stat().st_mtime, x[1]))

    return requests


async def serve_requests(portals: str = str(portals_dir), poll_interval: float = 0.1):
    """Serve image generation requests from portals directory"""
    logger.info("serving requests from %s (poll interval %.1f seconds)", portals, poll_interval)

    queue_processor_task = asyncio.create_task(process_image_queue())

    # Process existing requests first
    known_requests = find_todo_requests(portals)
    for portal, req_name in known_requests:
        logger.debug("Initial request detected: %s in %s", req_name, portal)
        await process_request(portals, portal, req_name)

    known_requests_set = set(known_requests)

    while True:
        try:
            new_requests = find_todo_requests(portals)
            for portal, req_name in new_requests:
                if (portal, req_name) in known_requests_set:
                    continue
                logger.debug("New request detected: %s in %s", req_name, portal)
                await process_request(portals, portal, req_name)

            known_requests_set = set(new_requests)

        except (asyncio.CancelledError, KeyboardInterrupt):
            logger.info("Serve requests task cancelled.")
            break
        except Exception as e:
            logger.exception("Error during request serving loop: %s", e)

        # Wait before next poll
        await asyncio.sleep(poll_interval)

    # Wait for the queue processor to finish if the server task is cancelled
    first = True
    while job is not None and not image_queue.empty():
        if first:
            logger.info("Waiting for queue processor to finish remaining jobs...")
            first = False
        await asyncio.sleep(1)
    queue_processor_task.cancel()
    await queue_processor_task
    logger.info("Server shutdown complete.")


def setup_args(arg):
    """Set up the command-line arguments"""
    arg("-p", "--portals", help="Directory of portals")
    arg("-i", "--poll-interval", type=float, help="Polling interval in seconds")


if __name__ == "__main__":
    main.go(serve_requests, setup_args)
