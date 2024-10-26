#!/usr/bin/env python3

"""
Estimates the age of individuals in images using the dima806/facial_age_image_detection model.
"""

import sys
import logging
from typing import IO, TextIO
from io import BytesIO

from PIL import Image
import transformers
import requests

from ally import main, logs

__version__ = "0.1.0"

logger = logs.get_logger()

model = None
transforms = None


def load_model():
    """Initialize the model and transforms."""
    global model, transforms
    model = transformers.ViTForImageClassification.from_pretrained('dima806/facial_age_image_detection')
    transforms = transformers.ViTImageProcessor.from_pretrained('dima806/facial_age_image_detection')


def estimate_age(image_path: str) -> str:
    """
    Estimates the age of an individual in the given image.
    :param image_path: Path to the image file
    :return: Detected age bin (e.g., "01", "02-03", etc.)
    """
    # Load the image
    image = Image.open(image_path)

    # Transform the image and pass it through the model
    inputs = transforms(images=image, return_tensors='pt')
    output = model(**inputs)

    # Get the predicted class probabilities and class labels
    proba = output.logits.softmax(1)
    preds = proba.argmax(1)
    prediction = model.config.id2label[preds.item()]

    # Return the prediction
    return prediction


def process_images(istream: TextIO, ostream: TextIO) -> None:
    """Processes images and estimates ages from stdin to stdout."""
    load_model()
    for line in istream:
        image_path = line.strip()
        if not image_path or image_path.startswith('#'):
            continue
        prediction = estimate_age(image_path)
        ostream.write(f"{prediction}\t{image_path}\n")


def setup_args(arg):
    """Setup the arguments for the script."""


if __name__ == '__main__':
    main.go(process_images, setup_args)

# Here's how you can adapt the provided code to use the `dima806/facial_age_image_detection` model from Hugging Face:

# ### Key Changes:
# 1. **Model Initialization**:
# - The model and transforms are initialized with `'dima806/facial_age_image_detection'` instead of `'civitai/age-vit'`.
# - The `ViTImageProcessor` is used with `images=image` to match the newer interface.
# - Note: This model predicts specific age bins, not just "minor" or "adult".
#
# 2. **Prediction Handling**:
# - The return type of `estimate_age` is adjusted to return the detected age bin as a string, reflecting the model's output.
# - The `estimate_age` function uses `model.config.id2label[preds.item()]` to get the predicted age bin from the model's configuration.
#
# Ensure to adjust any import paths or utilities (like `ally` or `logs`) to match your environment. This script reads image pathnames from `stdin`, one per line, and outputs the detected age information to `stdout` in TSV format, with the filename in the right-most column.
#
# ### Example Usage:
# To run the script, save it as `age_estimate_dima806.py` and execute it using Python. Pass image pathnames to `stdin`, one per line. The script writes the detected age bins and corresponding filenames to `stdout`.

# # Example command to run the script
# # $ echo "path/to/image1.jpg\npath/to/image2.jpg" | python age_estimate_dima806.py

# This command feeds image pathnames to the script and outputs the detected age information. Ensure to replace `"path/to/image1.jpg"` and `"path/to/image2.jpg"` with actual pathnames to images you want to process.

