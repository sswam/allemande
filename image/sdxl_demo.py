#!/usr/bin/env python3-allemande

"""
A simple demo script for Stable Diffusion XL (SDXL) text-to-image generation using a local model.
"""

import sys
import logging
from typing import TextIO, Optional

from argh import arg
from diffusers import StableDiffusionXLPipeline, AutoencoderKL
import torch

from ally import main

__version__ = "0.1.4"

logger = main.get_logger()

MODEL_PATH = "/opt/models/image/sd/cyberrealisticXL_v22.safetensors"
VAE_PATH = "/opt/models/image/sd-vae/sdxl_vae.safetensors"

def generate_image(
    prompt: str,
    output_path: str,
    negative_prompt: str = "",
    seed: Optional[int] = None,
    cfg_scale: float = 7.5,
    width: int = 1024,
    height: int = 1024,
    lowvram: bool = False,
    cpu: bool = False,
) -> None:
    """Generate an image using local SDXL model based on the given prompt."""
    options = {
        "torch_dtype": torch.float16,
        "use_safetensors": True,
        "variant": "fp16",
        "local_files_only": True
    }

    if lowvram:
        options.update({
            "load_in_8bit": True,
            "device_map": "auto"
        })

    pipe = StableDiffusionXLPipeline.from_single_file(MODEL_PATH, **options)

    # Load VAE if it's not included in the main model file
    if not hasattr(pipe, 'vae') or pipe.vae is None:
        vae = AutoencoderKL.from_single_file(VAE_PATH, use_safetensors=True)
        pipe.vae = vae

    if not cpu:
        pipe.to("cuda")

    generator = torch.Generator("cuda").manual_seed(seed) if seed is not None else None

    image = pipe(
        prompt=prompt,
        negative_prompt=negative_prompt,
        generator=generator,
        guidance_scale=cfg_scale,
        width=width,
        height=height,
    ).images[0]

    image.save(output_path)
    logger.info(f"Image saved to {output_path}")

@arg("--output", help="output image file path")
@arg("--negative-prompt", help="negative prompt for image generation")
@arg("--seed", help="random seed for reproducibility")
@arg("--cfg-scale", help="classifier-free guidance scale")
@arg("--width", help="width of the generated image")
@arg("--height", help="height of the generated image")
@arg("--lowvram", help="use 8-bit precision for low VRAM usage", default=False)
@arg("--cpu", help="run on CPU, it's gonna be slow", default=False)
def sdxl_demo(
    *args,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    output: str = "output.png",
    negative_prompt: str = "",
    seed: Optional[int] = None,
    cfg_scale: float = 7.5,
    width: int = 1024,
    height: int = 1024,
    lowvram: bool = False,
    cpu: bool = False,
) -> None:
    """
    A simple demo script for Stable Diffusion XL (SDXL) text-to-image generation using a local model.
    """
    get, put = main.io(istream, ostream)

    prompt = " ".join(args) if args else ""
    if not prompt:
        put("Enter a text prompt for image generation:")
        prompt = get()

    put(f"Generating image for prompt: '{prompt}'")
    generate_image(
        prompt,
        output,
        negative_prompt=negative_prompt,
        seed=seed,
        cfg_scale=cfg_scale,
        width=width,
        height=height,
        lowvram=lowvram,
    )
    put(f"Image generated and saved to: {output}")

if __name__ == "__main__":
    main.run(sdxl_demo)
