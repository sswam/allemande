#!/usr/bin/env python3-allemande

"""
An image generation script using SDXL to create images from a prompt.
"""

import os
import sys
import random
from typing import TextIO, List, Optional
from PIL import Image
from PIL.PngImagePlugin import PngInfo
from pathlib import Path
import re

from argh import arg
import torch
import diffusers


from ally import main, text

__version__ = "0.1.6"

logger = main.get_logger()

# Disable automatic downloads
os.environ["HF_HUB_OFFLINE"] = "1"

IMAGE_MODEL = os.environ["IMAGE_MODEL"]
IMAGE_VAE = os.environ.get("IMAGE_VAE")
IMAGE_TEXT_ENCODER = None  # os.environ.get("IMAGE_TEXT_ENCODER")  # TODO
IMAGE_SAMPLER = os.environ.get("IMAGE_SAMPLER", "DPM++ 2M")
IMAGE_SCHEDULER = os.environ.get("IMAGE_SCHEDULER", "Karras")


sampler_name_mapping = {
    "DPM++ 2M": "DPMSolverMultistep",
    "DPM++ 2M Karras": "DPMSolverMultistep",
    "DDIM": "DDIM",
    "DPM++ 2S a Karras": "DPMSolverSinglestep",
    "Euler": "EulerDiscrete",
    "Euler a": "EulerAncestralDiscrete",
    "Heun": "HeunDiscrete",
    "KDPM2": "KDPM2Discrete",
    "KDPM2 a": "KDPM2AncestralDiscrete",
    "LMS": "LMSDiscrete",
    "PNDM": "PNDM",
}


def load_pipeline(img2img: bool = False):
    if img2img:
        pipeline_class = diffusers.StableDiffusionXLImg2ImgPipeline
    else:
        pipeline_class = diffusers.StableDiffusionXLPipeline

    pipe = pipeline_class.from_single_file(
        Path(IMAGE_MODEL),
        use_safetensors=True,
        variant="fp16",
        torch_dtype=torch.float16,
        local_files_only=True,
    )

    # Load VAE if it's not included in the main model file
    if not hasattr(pipe, "vae") or pipe.vae is None:
        vae = AutoencoderKL.from_single_file(IMAGE_VAE, use_safetensors=True)
        pipe.vae = vae

    pipe = pipe.to("cuda")

    pipe.scheduler = setup_scheduler(pipe.scheduler.config)
    #     scheduler_name = sampler_name_mapping.get(IMAGE_SAMPLER)
    #     if scheduler_name:
    #         scheduler_class = getattr(diffusers.schedulers, scheduler_name)
    #         pipe.scheduler = scheduler_class.from_config(pipe.scheduler.config)
    #     else:
    #         logger.warning(f"Unknown IMAGE_SAMPLER '{IMAGE_SAMPLER}'. Using default scheduler.")

    return pipe


def setup_scheduler(scheduler_config):
    """Setup the scheduler based on the configuration"""
    sampler_key = sampler_name_mapping.get(IMAGE_SAMPLER, IMAGE_SAMPLER)
    try:
        scheduler_name = f"{sampler_key}Scheduler"
        scheduler_class = getattr(diffusers.schedulers, scheduler_name)

        # Check if the scheduler_class supports the 'beta_schedule' parameter
        init_params = scheduler_class.__init__.__code__.co_varnames
        if "beta_schedule" in init_params:
            scheduler = scheduler_class.from_config(
                scheduler_config, beta_schedule=IMAGE_SCHEDULER.lower()
            )
        else:
            logger.warning(
                f"Scheduler '{scheduler_name}' does not support 'beta_schedule' parameter"
            )
            scheduler = scheduler_class.from_config(scheduler_config)

        return scheduler
    except AttributeError as e:
        logger.error(f"Scheduler '{scheduler_name}' not found in diffusers.schedulers")
        raise e


def generate_image(
    prompt: str = "",
    negative_prompt: str = "",
    seed: int|None = None,
    steps: int = 30,
    cfg_scale: float = 7.0,
    width: int = 1024,
    height: int = 1024,
    denoising_strength: float = 0.75,
    source_image: Image.Image|None = None,
    output_path: str|None = None,
    image_count: int = 0,
) -> None:
    """Generate an image from the given prompt and parameters, and save it."""
    pipe = load_pipeline(img2img=source_image is not None)

    seed = seed or random.randint(0, 2**32 - 1)
    seed += image_count

    if output_path is None:
        output_path = get_filename(image_count, seed, prompt)

    pipe = load_pipeline(img2img=source_image is not None)

    generator = torch.Generator("cuda").manual_seed(seed)

    prompt = text.squeeze(prompt)
    negative_prompt = text.squeeze(negative_prompt)

    kwargs = {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "num_inference_steps": steps,
        "guidance_scale": cfg_scale,
        "generator": generator,
        "width": width,
        "height": height,
    }

    if source_image:
        kwargs["image"] = source_image
        kwargs["strength"] = denoising_strength

    image = pipe(**kwargs).images[0]

    model_name = Path(IMAGE_MODEL).stem
    model_hash = "-"  # TODO: Get the model hash

    # Save parameters in PNG metadata
    metadata = PngInfo()
    params = f"{prompt}\n" \
            "Negative prompt: {negative_prompt}\n" \
            "Steps: {steps}, Sampler: {IMAGE_SAMPLER}, Schedule type: {IMAGE_SCHEDULER}, " \
            "CFG scale: {cfg_scale}, Seed: {seed}, Size: {width}x{height}, " \
            "Model hash: {model_hash}, Model: {model_name}"
    # TODO VAE? Text encoder?
    if source_image:
        params += f", Source image: {source_image}, Denoising strength: {denoising_strength}"
    params += ", Generator: {prog} {__version__}"

    metadata.add_text("parameters", params)

    image.save(output_path, pnginfo=metadata)
    logger.info(f"Image saved to {output_path}")

    return seed


def resize_and_crop(
    image: Image.Image, target_width: int, target_height: int
) -> Image.Image:
    """Resize and crop the image to fit the target dimensions."""
    aspect_ratio = target_width / target_height
    img_aspect_ratio = image.width / image.height

    if img_aspect_ratio > aspect_ratio:
        # Image is wider, crop width
        new_width = int(image.height * aspect_ratio)
        left = (image.width - new_width) // 2
        image = image.crop((left, 0, left + new_width, image.height))
    elif img_aspect_ratio < aspect_ratio:
        # Image is taller, crop height
        new_height = int(image.width / aspect_ratio)
        top = (image.height - new_height) // 2
        image = image.crop((0, top, image.width, top + new_height))

    return image.resize((target_width, target_height), Image.LANCZOS)


def read_chunk(get: TextIO, break_lines: int) -> str:
    """ Read a chunk of text from the input stream, separated by blank lines. """
    prompt = ""
    count_blank = 0
    while True:
        line = get()
        if line is None:
            break
        line = line.rstrip()
        if line and count_blank:
            prompt += "\n" * count_blank
            count_blank = 0
        if line:
            prompt += line + "\n"
        else:
            count_blank += 1
        if count_blank >= break_lines:
            break
    return prompt


def get_filename(image_count: int, seed: int, prompt: str) -> str:
    """ Get the output filename based on the prompt. """
    print(f"get_filename: {image_count=}, {seed=}, {prompt=}")
    ext = ".png"
    filename = f"{image_count:05d}_{seed:08d}_"
    max_len = 255 - len(filename + ext)
    prompt = re.sub(r"[^a-zA-Z0-9]+", " ", prompt)
    prompt = text.squeeze(prompt)[:max_len]
    prompt = prompt.replace(" ", "_")
    filename += prompt + ext
    return filename


@arg("-s", "--seed", help="random seed")
@arg("-n", "--steps", help="number of inference steps")
@arg("-c", "--cfg-scale", help="CFG scale")
@arg("-w", "--width", help="image width")
@arg("-h", "--height", help="image height")
@arg("-x", "--negative-prompt", help="negative prompt")
@arg("-d", "--denoising-strength", help="denoising strength for img2img")
@arg("-b", "--break-lines", help="number of blank lines between prompts")
def image(
    input: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    seed: int | None = None,
    steps: int = 30,
    cfg_scale: float = 7.0,
    width: int = 1024,
    height: int = 1024,
    negative_prompt: str = "",
    denoising_strength: float = 0.5,
    break_lines: int = 0,
) -> None:
    """
    Generate images from a prompt using SDXL.
    """
    get, put = main.io(input, output)

    image_count = 0
    while True:
        chunk = read_chunk(get, break_lines)

        if chunk == "":
            break

        parts = chunk.split("\t")
        parts.reverse()
        parts = parts + [None] * (3 - len(parts))
        prompt, output_path, source_image_path = parts

        source_image = None
        if source_image_path:
            source_image = Image.open(source_image_path)
            source_image = resize_and_crop(source_image, width, height)

        generate_image(
            prompt = prompt,
            negative_prompt = negative_prompt,
            seed = seed,
            steps = steps,
            cfg_scale = cfg_scale,
            width = width,
            height = height,
            denoising_strength = denoising_strength,
            source_image = source_image,
            output_path = output_path,
            image_count = image_count,
        )

        image_count += 1

    logger.info(f"Generated {image_count} image(s).")


if __name__ == "__main__":
    main.run(image)
