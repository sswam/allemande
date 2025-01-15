#!/usr/bin/env python3-allemande

"""
A Python module / script to generate images using the Stable Diffusion WebUI API.
"""

import os
import datetime
import base64
import random
from pathlib import Path
import signal
import asyncio
import json
import re

import aiohttp
from tqdm import tqdm  # type: ignore

from ally import main, text  # type: ignore

__version__ = "0.1.0"

logger = main.get_logger()

API_URL = "http://127.0.0.1:7860/sdapi/v1/txt2img"


async def generate_image(session, params):
    """Send a request to the API and return the response."""
    async with session.post(API_URL, json=params) as response:
        return await response.json()


def remove_comments(text):
    """Remove comments from the text."""
    return re.sub(r"#.*", "", text, flags=re.MULTILINE)


async def a1111_client(
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
    pony: float = 0.0,
    adetailer: list[str] = None,
    pag: bool = False,
    hires: float = 0.0,
    ad_mask_k_largest = 0,
    model: str = "",
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

    prompt = text.squeeze(remove_comments(prompt))
    negative_prompt = text.squeeze(remove_comments(negative_prompt))

    if pony:
        prompt, negative_prompt = pony_biolerplate(pony, prompt, negative_prompt)

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
        "override_settings": {},
    }

    if model:
        params["override_settings"]["sd_model_checkpoint"] = model

    if hires:
        hires_fix_add_params(params, hires)

    if adetailer:
        adetailer_add_params(params, adetailer, ad_mask_k_largest)

    if pag:
        perturbed_attention_guidance_add_params(params)

    interrupt_flag = False

    def signal_handler(_signum, _frame):
        nonlocal interrupt_flag
        interrupt_flag = True

    try:
        signal.signal(signal.SIGINT, signal_handler)
        logger.debug("Generating %s images to %s", count, outdir)
        async with aiohttp.ClientSession() as session:
            i = None
            for i in tqdm(range(count), desc="Generating images"):
                if count == 1:
                    image_file = str(outdir/f"{stem}.png")
                else:
                    image_file = str(outdir/f"{stem}_{i:05}.png")
                if not clobber and os.path.exists(image_file):
                    logger.debug("Skipping existing file %s", image_file)
                    continue
                logger.debug("Generating image %s/%s", i + 1, count)
                params["seed"] = (seed + i) % 2**32
                response = await generate_image(session, params)
                if "images" not in response:
                    raise ValueError(f"Got no images in response: {json.dumps(response)}")
                image = base64.b64decode(response["images"][0])
                with open(image_file, "wb") as f:
                    f.write(image)
                logger.info("Generated %s", image_file)
                if interrupt_flag:
                    logger.info("Interrupted at %s images", i + 1)
                    break
                if sleep:
                    await asyncio.sleep(sleep)
            logger.debug("Generated %s images to %s", i + 1, outdir)
    except Exception as e:
        logger.error("Error: %s", e)
    finally:
        logger.debug("Exiting")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
    logger.debug("Done")


def pony_biolerplate(pony, prompt, negative_prompt):
    """Add pony boilerplate to the prompt and negative prompt."""
    pony1p = f"(score_9, score_8_up, score_7_up, score_6_up, score_5_up, score_4_up:{pony})\nBREAK\n"
    prompt = f"{pony1p}{prompt}"
#    pony1n = f"(score_6, score_5, score_4:{pony})\nBREAK\n"
    pony1n = f"score_6, score_5, score_4\nBREAK\n"
    negative_prompt = f"{pony1n}{negative_prompt}"
    return prompt, negative_prompt


def hires_fix_add_params(params, scale, denoising_strength=0.3, steps=None):
    if steps is None:
        steps = max(1, round(denoising_strength * params["steps"] + 0.5 - 1e-6))
    params.update(
        {
            "enable_hr": True,
            "hr_scale": scale,
#            "hr_upscaler": "Lanczos",
            "hr_upscaler": "ESRGAN_4x",
            "denoising_strength": denoising_strength,
            "hr_scheduler": params["scheduler"],
            "hr_second_pass_steps": steps,
        }
    )


def adetailer_add_params(params, adetailer, ad_mask_k_largest):
    """Add adetailer parameters to the params."""
    if not "alwayson_scripts" in params:
        params["alwayson_scripts"] = {}

    # I copied these parameters from the API payload extension.
    # Most of them are defaults, and we could likely remove them.
    # It might be good if ad_denoising_strength and
    # ad_inpaint_only_masked_padding can vary, but for now they are fixed.

    args = [True, False]
    params["alwayson_scripts"]["ADetailer"] = {"args": args}
    for model in adetailer:
        args.append(
            {
#                "ad_denoising_strength": 0.3,
                "ad_denoising_strength": 0.4,
                "ad_cfg_scale": 7,
                "ad_checkpoint": "Use same checkpoint",
                "ad_clip_skip": 1,
                "ad_confidence": 0.3,
                "ad_controlnet_guidance_end": 1,
                "ad_controlnet_guidance_start": 0,
                "ad_controlnet_model": "None",
                "ad_controlnet_module": "None",
                "ad_controlnet_weight": 1,
                "ad_dilate_erode": 4,
                "ad_inpaint_height": 1024,
                "ad_inpaint_only_masked": True,
                "ad_inpaint_only_masked_padding": 64 * params.get("hr_scale", 1),
                "ad_inpaint_width": 1024,
                "ad_mask_blur": 16 * params.get("hr_scale", 1),
                "ad_mask_k_largest": ad_mask_k_largest,
                "ad_mask_max_ratio": 1,
                "ad_mask_merge_invert": "None",
                "ad_mask_min_ratio": 0,
                "ad_model": model,
                "ad_model_classes": "",
                "ad_negative_prompt": "",
                "ad_noise_multiplier": 1,
                "ad_prompt": "",
                "ad_restore_face": False,
                "ad_sampler": "DPM++ 2M",
                "ad_scheduler": "Use same scheduler",
                "ad_steps": 28,
                "ad_tab_enable": True,
                "ad_use_cfg_scale": False,
                "ad_use_checkpoint": False,
                "ad_use_clip_skip": False,
                "ad_use_inpaint_width_height": False,
                "ad_use_noise_multiplier": False,
                "ad_use_sampler": False,
                "ad_use_steps": False,
                "ad_use_vae": False,
                "ad_vae": "Use same VAE",
                "ad_x_offset": 0,
                "ad_y_offset": 0,
                "is_api": [],
            }
        )


def perturbed_attention_guidance_add_params(params):
    """Add perturbed attention guidance parameters to the params."""
    if not "alwayson_scripts" in params:
        params["alwayson_scripts"] = {}

    # This is a bit unintelligible as the extension does not name its parameters.
    # I just copied them from the API payload extension.
    params["alwayson_scripts"]["Incantations"] = (
        {
            "args": [
                False,
                11,
                0,
                150,
                False,
                1,
                0.8,
                3,
                0,
                0,
                150,
                4,
                True,
                5,
                0,
                150,
                False,
                "Constant",
                0,
                100,
                True,
                False,
                False,
                2,
                0.1,
                0.5,
                0,
                "",
                0,
                25,
                1,
                False,
                False,
                False,
                "BREAK",
                "-",
                0.2,
                10,
            ]
        },
    )


def setup_args(arg):
    """Setup the command line arguments."""
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
    arg("-P", "--pony", help="add pony boilerplate; strength")
    arg("-D", "--adetailer", nargs="*", help="use adetailer with specified models")
    arg("-g", "--pag", help="use perturbed attention guidance", action="store_true")
    arg("-u", "--hires", help="hires fix / upscale by factor")
    arg("--ad-mask-k-largest", type=int, help="adetailer mask limit to k largest matches")
    arg("-m", "--model", help="stable diffusion model checkpoint")


if __name__ == "__main__":
    main.go(a1111_client, setup_args)
