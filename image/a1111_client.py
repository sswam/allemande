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
    output_file: str = "",
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
) -> None:
    """
    Generate images using the Stable Diffusion WebUI API.
    """
    if not output_file:
        now = datetime.datetime.now()
        output_file = f"output_{now.strftime('%Y%m%d_%H%M%S')}.png"
    outdir = Path(output_file).parent
    stem = Path(output_file).stem

    if seed == -1:
        seed = random.randint(0, 2**32 - 1)

    prompt = text.squeeze(prompt)
    negative_prompt = text.squeeze(negative_prompt)

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
        async with aiohttp.ClientSession() as session:
            for i in tqdm(range(count), desc="Generating images"):
                image_file = f"{outdir}/{stem}_{i:05}.png"
                params["seed"] = (seed + i) % 2**32
                response = await generate_image(session, params)
                image = base64.b64decode(response["images"][0])
                with open(image_file, "wb") as f:
                    f.write(image)
                logger.info(f"{image_file}")
                if interrupt_flag:
                    logger.info(f"Interrupted at {i+1} images")
                    break
    finally:
        signal.signal(signal.SIGINT, signal.SIG_DFL)


@arg("--prompt", help="prompt for image generation")
@arg("--negative-prompt", help="negative prompt for image generation")
@arg("--seed", type=int, help="seed for image generation")
@arg("--sampler-name", help="sampler name")
@arg("--scheduler", help="scheduler")
@arg("--steps", type=int, help="number of steps")
@arg("--cfg-scale", type=float, help="cfg scale")
@arg("--width", type=int, help="image width")
@arg("--height", type=int, help="image height")
@arg("--count", type=int, help="number of images to generate")
def a1111_client(
    output_file: str = "",
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
) -> None:
    """
    Generate images using the Stable Diffusion WebUI API.
    """
    asyncio.run(
        a1111_client_async(
            output_file=output_file,
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
        )
    )

if __name__ == "__main__":
    main.run(a1111_client)
