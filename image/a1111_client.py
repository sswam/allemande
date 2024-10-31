#!/usr/bin/env python3

"""
A Python module / script to generate images using the Stable Diffusion WebUI API.
"""

import os
import sys
import json
import logging
import datetime
import base64
import random
from pathlib import Path
import signal

import aiohttp
import asyncio
from argh import arg
from tqdm import tqdm

from ally import main, text

__version__ = "0.1.0"

logger = main.get_logger()

API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"


async def generate_image(session, params):
    """Send a request to the API and return the response."""
    async with session.post(API_URL, json=params) as response:
        return await response.json()


async def a1111_client_async(
    output: str = "",
    prompt: str = "",
    negative_prompt: str = "",
    seed: int = -1,
    sampler_name: str = "DPM++ 2M",
    scheduler: str = "Karras",
    steps: int = 15,
    cfg_scale: float = 7,
    width: int = 1024,
    height: int = 1024,
    count: int = 1,
    sleep: float = 0.0,
    clobber: bool = False,
    pony: bool = False,
) -> None:
    """
    Generate images using the Stable Diffusion WebUI API.
    """
    if not output:
        now = datetime.datetime.now()
        output = f"output_{now.strftime('%Y%m%d_%H%M%S')}.png"
    outdir = Path(output).parent
    stem = Path(output).stem

    if seed == -1:
        seed = random.randint(0, 2**32 - 1)

    prompt = text.squeeze(prompt)
    negative_prompt = text.squeeze(negative_prompt)

    if pony:
        prompt, negative_prompt = pony_biolerplate(prompt, negative_prompt)

    params = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "sampler_name": sampler_name,
        "scheduler": scheduler,
        "steps": steps,
        "cfg_scale": cfg_scale,
        "width": width,
        "height": height,
        "do_not_save_grid": True,
    }

    interrupt_flag = False

    def signal_handler(signum, frame):
        nonlocal interrupt_flag
        interrupt_flag = True

    try:
        signal.signal(signal.SIGINT, signal_handler)
        logger.debug(f"Generating {count} images to {outdir}")
        async with aiohttp.ClientSession() as session:
            for i in tqdm(range(count), desc="Generating images"):
                image_file = f"{outdir}/{stem}_{i:05}.png"
                if not clobber and os.path.exists(image_file):
                    logger.debug(f"Skipping existing file {image_file}")
                    continue
                logger.debug(f"Generating image {i+1}/{count}")
                params["seed"] = (seed + i) % 2**32
                response = await generate_image(session, params)
                image = base64.b64decode(response["images"][0])
                with open(image_file, "wb") as f:
                    f.write(image)
                logger.info(f"{image_file}")
                if interrupt_flag:
                    logger.info(f"Interrupted at {i+1} images")
                    break
                if sleep:
                    await asyncio.sleep(sleep)
            logger.debug(f"Generated {i+1} images to {outdir}")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        logger.debug("Exiting")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    logger.debug("Done")


def pony_biolerplate(prompt, negative_prompt):
    """Add pony boilerplate to the prompt and negative prompt."""
    pony1p = "score_9, score_8_up, score_7_up, score_6_up, score_5_up, score_4_up, "
    prompt = f"{pony1p} {prompt}"
    pony1n = "score_6, score_5, score_4, "
    negative_prompt = f"{pony1n} {negative_prompt}"
    return prompt, negative_prompt


def a1111_client(
    output: str = "",
    prompt: str = "",
    negative_prompt: str = "",
    seed: int = -1,
    sampler_name: str = "DPM++ 2M",
    scheduler: str = "Karras",
    steps: int = 30,
    cfg_scale: float = 7,
    width: int = 1024,
    height: int = 1024,
    count: int = 1,
    sleep: float = 0.0,
    clobber: bool = False,
    pony: bool = False,
) -> None:
    """
    Generate images using the Stable Diffusion WebUI API.
    """
    asyncio.run(
        a1111_client_async(
            output=output,
            prompt=prompt,
            negative_prompt=negative_prompt,
            seed=seed,
            sampler_name=sampler_name,
            scheduler=scheduler,
            steps=steps,
            cfg_scale=cfg_scale,
            width=width,
            height=height,
            count=count,
            sleep=sleep,
            clobber=clobber,
            pony=pony,
        )
    )


def setup_args(arg):
    arg("-o", "--output", help="output file (png)")
    arg("-p", "--prompt", help="prompt for image generation")
    arg("-n", "--negative-prompt", help="negative prompt for image generation")
    arg("-s", "--seed", type=int, help="seed for image generation")
    arg("--sampler-name", help="sampler name")
    arg("--scheduler", help="scheduler")
    arg("-i", "--steps", type=int, help="number of steps")
    arg("-C", "--cfg-scale", type=float, help="cfg scale")
    arg("-W", "--width", type=int, help="image width")
    arg("-H", "--height", type=int, help="image height")
    arg("-c", "--count", type=int, help="number of images to generate")
    arg("-S", "--sleep", type=float, help="sleep between generations")
    arg("-X", "--clobber", help="overwrite existing files", action="store_true")
    arg("-P", "--pony", help="add pony boilerplate", action="store_true")
 

if __name__ == "__main__":
    main.go(a1111_client, setup_args)
