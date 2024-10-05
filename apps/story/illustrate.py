#!/usr/bin/env python3

"""
This module creates images for a document using an AI image generator.

Example:

    illustrate --debug --prompt0 "cartoony, watercolor like monet," story.md --width 800 --height 600 --count 4
"""

import os
import re
import math
import dataclasses
from dataclasses import dataclass
import importlib.util

from argh import arg
# pylint: disable=no-member
import sh  # type: ignore
from bs4 import BeautifulSoup
import inflect

from ally import main  # type: ignore

__version__ = "0.1.3"

logger = main.get_logger()
p = inflect.engine()


# pylint: disable=too-many-instance-attributes
@dataclass
class Options:
    """ Options for the illustrate command. """
    input_file: str
    output_dir: str
    model: str|None
    width: int
    height: int
    prompt0: str
    prompt1: str
    negative: str
    module: str
    count: int
    fix_dimensions: bool
    pony: bool


# pylint: disable=too-many-arguments,too-many-positional-arguments
@arg("input_file", help="Input file name")
@arg("-o", "--output-dir", help="Output directory for images")
@arg("-m", "--model", help="AI model to use")
@arg("-w", "--width", help="Default image width")
@arg("-h", "--height", help="Default image height")
@arg("-p", "--prompt0", help="Extra prompt guidance added at the start")
@arg("-q", "--prompt1", help="Extra prompt guidance added at the end")
@arg("-n", "--negative", help="Negative prompt")
@arg("-c", "--count", help="Number of images to generate for each prompt")
@arg("-f", "--fix-dimensions", help="Use the closest happy SDXL dimensions")
@arg("-F", "--no-fix-dimensions", dest="fix_dimensions", action="store_false")
@arg("-P", "--pony", help="Add prompting boilerplate for Pony and Pony-derived models")
def illustrate(
    input_file: str,
    output_dir: str = ".",
    model: str|None = None,
    width: int = 800,
    height: int = 600,
    prompt0: str = "",
    prompt1: str = "",
    negative: str = "",
    module: str = "",
    count: int = 1,
    fix_dimensions: bool = True,
    pony: bool = False,
) -> None:
    """
    Create images for a document using an AI image generator.
    """
    if not input_file:
        raise ValueError("Input file is required")
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' does not exist")

    os.makedirs(output_dir, exist_ok=True)

    mod = None
    if module:
        mod = import_module_from_file(module)

    options = Options(
        input_file=input_file,
        output_dir=output_dir,
        model=model,
        width=width,
        height=height,
        prompt0=prompt0,
        prompt1=prompt1,
        negative=negative,
        module=mod,
        count=count,
        fix_dimensions=fix_dimensions,
        pony=pony,
    )

    process_file(options)


def check_markdown_image(line: str) -> list[tuple[str, str, int | None, int | None]]:
    """ Check for markdown images in a line of text. """
    pattern = r'!\[(.+?)\]\((.+?)(?: "(.*?)")?\)(?:(?:<!--)?{.*?\bwidth=(\d+).*?\bheight=(\d+).*?})?'
    matches = re.finditer(pattern, line)
    results = []
    for match in matches:
        alt_text, filename, title, width, height = match.groups()
        width = int(width) if width else None
        height = int(height) if height else None
        logger.debug(
            f"Found markdown image: alt={alt_text}, title={title}, file={filename}, width={width}, height={height}"
        )
        results.append((str(alt_text or title or ""), str(filename), width, height))
    return results


def check_html_image(line: str) -> list[tuple[str, str, int | None, int | None]]:
    """ Check for HTML images in a line of text. """
    soup = BeautifulSoup(line, "html.parser")
    images = soup.find_all("img")
    results = []
    for img in images:
        alt_text = img.get("alt", "")
        title = img.get("title", "")
        filename = img.get("src", "")
        width = (
            int(img.get("width"))
            if img.get("width") and img.get("width").isdigit()
            else None
        )
        height = (
            int(img.get("height"))
            if img.get("height") and img.get("height").isdigit()
            else None
        )
        logger.debug(
            f"Found HTML image: alt={alt_text}, file={filename}, width={width}, height={height}"
        )
        results.append((str(alt_text or title), str(filename), width, height))
    return results


def import_module_from_file(file_path):
    spec = importlib.util.spec_from_file_location("module_name", file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def squeeze_prompt(text: str) -> str:
    text = re.sub(r"\s*,[, ]*", ", ", text).strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def process_file(options: Options) -> None:
    """ Process the input file, generating images for each image found. """
    fmt = os.path.splitext(options.input_file)[1].lower()[1:]

    with open(options.input_file, "r", encoding="utf-8") as file:
        for line in file:
            if fmt == "md":
                images = check_markdown_image(line)
            else:
                images = check_html_image(line)

            if not images:
                continue

            for image_info in images:
                alt_text, filename, width, height = image_info

                width = width or options.width
                height = height or options.height

                if options.fix_dimensions:
                    width, height = adjust_dimensions(
                        width, height, options.width, options.height
                    )

                prompt = f"{options.prompt0} {alt_text} {options.prompt1}".strip()
                negative = options.negative

                # allow modifying the prompt and negative prompt with Python code
                if options.module:
                    logger.debug(f"Before: {prompt=}, {negative=}")
                    prompt, negative = options.module.prompts(prompt, negative)
                    prompt, negative = squeeze_prompt(prompt), squeeze_prompt(negative)
                    logger.debug(f"After: {prompt=}, {negative=}")

                # actually options and update some things
                image_options = dataclasses.replace(
                        options,
                        width=width,
                        height=height,
                )

                generate_image(
                    prompt,
                    negative,
                    filename,
                    image_options,
                )


sdxl_preferred_dimensions = {
    (1024, 1024),
    (1152, 896),
    (896, 1152),
    (1216, 832),
    (832, 1216),
    (1344, 768),
    (768, 1344),
    (1536, 640),
    (640, 1536),
}


def adjust_dimensions(
    width: int | None, height: int | None, default_width: int, default_height: int
) -> tuple[int, int]:
    """
    Choose the closest dimensions to the aspect ratio, from sdxl_preferred_dimensions.
    To be mathematical, we take the log of the ratio between the aspect ratios,
    e.g. log2 2/1 would be 1, and log2 1/2 would be -1.
    """
    if width is None:
        width = default_width
    if height is None:
        height = default_height

    aspect = width / height
    best_dimensions = min(
        sdxl_preferred_dimensions, key=lambda d: abs(math.log((d[0] / d[1]) / aspect))
    )

    return best_dimensions


def generate_image(
    prompt: str,
    negative: str,
    filename: str,
    options: Options,
) -> None:
    """ Generate an image using the AI image generator. """
    output_path = os.path.join(options.output_dir, filename)

    images_txt = p.plural("image", options.count)

    logger.info(
        f"Generating {options.count} {images_txt} for {filename}: {prompt=}, {negative=}, dimensions={options.width}x{options.height}"
    )

    try:
        kwargs = {
            "output-file": output_path,
            "prompt": prompt,
            "width": options.width,
            "height": options.height,
            "sampler-name": "DPM++ 2M",
            "scheduler": "Karras",
            "steps": 15,
            "cfg-scale": 5,
            "count": options.count,
            "negative-prompt": negative,
        }
        if options.model is not None:
            kwargs["model"] = options.model
        if options.pony:
            kwargs["pony"] = True

        # run the a1111 stable diffusion webui client
        sh.a1111_client("-d", **kwargs)
    except sh.ErrorReturnCode as e:
        logger.error(f"Failed to generate image for {filename}: {prompt}")
        logger.error(f"Error: {e}")
        raise

    # symlink the first image, foo_00000.png, to foo.png
    numbered_output_path = numbered_image_name(output_path)
    if os.path.exists(output_path):
        logger.warning(f"Already exists: {output_path}")
    else:
        logger.info(f"Creating symlink: {output_path} -> {numbered_output_path}")
        os.symlink(numbered_output_path, output_path)


def numbered_image_name(filename: str, index: int = 0) -> str:
    """ Return the numbered image name for the given index. """
    stem, ext = os.path.splitext(filename)
    return f"{stem}_{index:05d}{ext}"


if __name__ == "__main__":
    main.run(illustrate)


# TODO:

# Note: many of the "TODOs" below don't belong in this tool,
#   we would create separate tools and use them from this tool.
#   But it's useful to think about them here.

# - Support multiple image generators
#   - SDXL, ComfyUi, our 'image' tool, etc.
#   - different types of models
#     - SD classic, SDXL, Flux, etc.
#   - 3rd-party API services: OpenAI, MidJourney, etc.
#   - this should be handled in our "image" tool, not here

# - Automatically choose the best image from each batch:
#      - ideally with reference to the prompt
#      - a generic aesthetic scoring model
#      - we can train our own scoring models, maybe per user
#      - the user can just choose
#      - mechanical turk, or similar
#        - it could be a pretty cushy job, just reviewing images!
#      - this should be handled in our "best" tool, not here

# - we could use the python lib version of a1111-client

# - sdxl_preferred_dimensions is only for SDXL (Stable Diffusion Extra Large).
#   If we support other models or image generators, we need to know their
#   preferred dimensions. This should be a separate tool / library function.
