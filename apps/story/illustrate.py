#!/usr/bin/env python3

"""
This module creates images for a document using an AI image generator.
"""

import os
import re
import math

from argh import arg
import sh
from bs4 import BeautifulSoup

from ally import main

__version__ = "0.1.2"

logger = main.get_logger()


# TODO automatically choose the best image from each batch


@arg("input_file", help="Input file name")
@arg("-o", "--output-dir", help="Output directory for images")
@arg("-m", "--model", help="AI model to use")
@arg("-w", "--width", help="Default image width")
@arg("-h", "--height", help="Default image height")
@arg("-p", "--prompt0", help="Extra prompt guidance added at the start")
@arg("-q", "--prompt1", help="Extra prompt guidance added at the end")
@arg("-c", "--count", help="Number of images to generate for each prompt")
# TODO option to add to the end of the prompt?
def illustrate(
    input_file: str,
    output_dir: str = ".",
    model: str|None = None,
    width: int = 1024,
    height: int = 1024,
    prompt0: str|None = None,
    prompt1: str|None = None,
    count: int = 1,
    #     istream: TextIO = sys.stdin,
    #     ostream: TextIO = sys.stdout,
) -> None:
    """
    Create images for a document using an AI image generator.
    """
    if not input_file:
        raise ValueError("Input file is required")
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"Input file '{input_file}' does not exist")

    os.makedirs(output_dir, exist_ok=True)

    process_file(input_file, output_dir, model, width, height, prompt0, prompt1, count)


def check_markdown_image(line: str) -> list[tuple[str, str, int|None, int|None]]:
    logger.debug(f"Checking markdown images: {line}")
    pattern = r'!\[(.+?)\]\((.+?)( "(.*?)")?\)(?:{.*?\bwidth=(\d+).*?\bheight=(\d+).*?})?'
    matches = re.finditer(pattern, line)
    results = []
    for match in matches:
        alt_text, filename, title, width, height = match.groups()
        width = int(width) if width else None
        height = int(height) if height else None
        logger.debug(f"Found markdown image: alt={alt_text}, title={title}, file={filename}, width={width}, height={height}")
        results.append((str(alt_text or title or ""), str(filename), width, height))
    return results


def check_html_image(line: str) -> list[tuple[str, str, int|None, int|None]]:
    logger.debug(f"Checking HTML images: {line}")
    soup = BeautifulSoup(line, 'html.parser')
    images = soup.find_all('img')
    results = []
    for img in images:
        alt_text = img.get('alt', '')
        title = img.get('title', '')
        filename = img.get('src', '')
        width = int(img.get('width')) if img.get('width') and img.get('width').isdigit() else None
        height = int(img.get('height')) if img.get('height') and img.get('height').isdigit() else None
        logger.debug(f"Found HTML image: alt={alt_text}, file={filename}, width={width}, height={height}")
        results.append((str(alt_text or title), str(filename), width, height))
    return results


def process_file(
    input_file: str,
    output_dir: str,
    model: str|None,
    default_width: int,
    default_height: int,
    prompt0: str|None,
    prompt1: str|None,
    count: int = 1,
) -> None:
    fmt = os.path.splitext(input_file)[1].lower()[1:]

    with open(input_file, "r") as file:
        for line in file:
            if fmt == "md":
                images = check_markdown_image(line)
            else:
                images = check_html_image(line)

            if not images:
                continue

            for image_info in images:
                alt_text, filename, width, height = image_info

                width, height = adjust_dimensions(
                    width, height, default_width, default_height
                )

                prompt = f"{prompt0} {alt_text} {prompt1}".strip()

                generate_image(prompt, filename, output_dir, model, width, height, count)


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


def adjust_dimensions(width: int|None, height: int|None, default_width: int, default_height: int) -> tuple[int, int]:
    if width is None:
        width = default_width
    if height is None:
        height = default_height

    # Choose the closest dimensions to the aspect ratio, from sdxl_preferred_dimensions.
    # To be mathematical, we take the log of the ratio between the aspect ratios,
    # e.g. log2 2/1 would be 1, and log2 1/2 would be -1.
    aspect = width / height
    best_dimensions = min(
        sdxl_preferred_dimensions, key=lambda d: abs(math.log((d[0] / d[1]) / aspect))
    )

    return best_dimensions


def generate_image(
    alt_text: str, filename: str, output_dir: str, model: str|None, width: int, height: int, count: int = 1
) -> None:
    output_path = os.path.join(output_dir, filename)

    # use inflection?
    images_txt = "image" if count == 1 else "images"
    logger.info(f"Generating {count} {images_txt}: prompt='{alt_text}', dimensions={width}x{height}")

    try:
        image_exists = os.path.isfile(output_path)

        if image_exists:
            logger.info(f"Image saved as: {output_path}")
        else:
            kwargs = {
                "o": output_path,
                "p": alt_text,
                "width": width,
                "height": height,
                "sampler-name": "DPM++ 2M",
                "scheduler": "Karras",
                "steps": 15,
                "cfg-scale": 5,
                "count": count,
            }
            if model is not None:
                kwargs["--model"] = model

            sh.a1111("-v", **kwargs)  # TODO could use the python lib version, as it's written in python

            logger.info(f"Image saved as: {output_path}")
    except sh.ErrorReturnCode as e:
        logger.error(f"Failed to generate image for: {alt_text}")
        logger.error(f"Error: {e}")
        raise


    # symlink foo_00000.png to foo.png
    numbered_output_path = numbered_image_name(output_path)
    if os.path.exists(output_path):
        logger.warning(f"Image already exists: {output_path}")
    else:
        logger.info(f"Creating symlink: {output_path} -> {numbered_output_path}")
        os.symlink(numbered_output_path, output_path)


def numbered_image_name(filename: str, index: int = 0) -> str:
    stem, ext = os.path.splitext(filename)
    return f"{stem}_{index:05d}{ext}"


if __name__ == "__main__":
    main.run(illustrate)
