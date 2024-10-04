#!/usr/bin/env python3

"""
This module creates images for a document using an AI image generator.
"""

import sys
import os
import re
from typing import TextIO
import math

from argh import arg
import sh

from ally import main
from ally.lazy import lazy

__version__ = "0.1.1"

logger = main.get_logger()


@arg("input_file", help="Input file name")
@arg("-o", "--output-dir", help="Output directory for images")
@arg("-m", "--model", help="AI model to use")
@arg("-w", "--width", type=int, help="Default image width")
@arg("-h", "--height", type=int, help="Default image height")
def illustrate(
    input_file: str,
    output_dir: str = ".",
    model: str = None,
    width: int = 1024,
    height: int = 1024,
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

    process_file(input_file, output_dir, model, width, height)


# TODO handle multiple images on one line, somehow?!  not yet

# TODO get title info too?


def check_markdown_image(line: str) -> tuple[str, str] | None:
    pattern = r"!\[(.+?)\]\((.+?)\)(?:{.*?\bwidth=(\d+).*?\bheight=(\d+).*?})?"
    match = re.search(pattern, line)
    if match:
        alt_text, filename = match.groups()
        width = int(width) if width else None
        height = int(height) if height else None
        return str(alt_text), str(filename), width, height
    return None


# TODO get title info too?


def check_html_image(line: str) -> tuple[str, str] | None:
    # TODO use an HTML parser or something, at a higher level?  later
    pattern = r'<img.*?alt="(.+?)".*?src="(.+?)".*?(?:\bwidth="(\d+)".*?\bheight="(\d+)")?.*?>'
    match = re.search(pattern, line, re.DOTALL)
    if match:
        alt_text, filename = match.groups()
        width = int(width) if width else None
        height = int(height) if height else None
        return str(alt_text), str(filename), width, height
    return None


def process_file(
    input_file: str,
    output_dir: str,
    model: str,
    default_width: int,
    default_height: int,
) -> None:
    fmt = os.path.splitext(input_file)[1].lower()[1:]

    with open(input_file, "r") as file:
        for line in file:
            if fmt == "md":
                image_info = check_markdown_image(line)
            else:
                image_info = check_html_image(line)

            if not image_info:
                continue

            alt_text, filename, width, height = image_info

            width, height = adjust_dimensions(width, height, default_width, default_height)

            generate_image(alt_text, filename, output_dir, model, width, height)


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


def adjust_dimensions(width, height, default_width, default_height):
    if width is None:
        width = default_width
    if height is None:
        height = default_height

    # Choose the closest dimensions to the aspect ratio, from sdxl_preferred_dimensions.
    # To be mathematical, we take the log of the ratio between the aspect ratios,
    # e.g. log2 2/1 would be 1, and log2 1/2 would be -1.
    aspect = width / height
    best_dimensions = min(sdxl_preferred_dimensions, key=lambda d: abs(math.log((d[0] / d[1]) / aspect)))

    return best_dimensions


def generate_image(
    alt_text: str, filename: str, output_dir: str, model: str, width: int, height: int
) -> None:
    output_path = os.path.join(output_dir, filename)

    logger.info(f"Generating image for: {alt_text}")
    try:
        sh.imagen(
            "-o", output_path,
            "-p", alt_text,
            "--width", str(width),
            "--height", str(height),
            "--sampler-name", "DPM++ 2M",
            "--scheduler", "Karras",
            "--steps", "30",
            "--cfg-scale", "7",
            "--count", "1",
            "--model", model,
        )
        logger.info(f"Image saved as: {output_path}")
    except sh.ErrorReturnCode as e:
        logger.error(f"Failed to generate image for: {alt_text}")
        logger.error(f"Error: {e}")
        raise
