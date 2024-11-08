#!/usr/bin/env python3-allemande

"""
Estimates the age of individuals in images using the Civitai/age-vit model.
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
    model = transformers.ViTForImageClassification.from_pretrained('civitai/age-vit')
    transforms = transformers.ViTImageProcessor.from_pretrained('civitai/age-vit')


def estimate_age(image_path: str) -> str:
    """
    Estimates the age of an individual in the given image.
    :param image_path: Path to the image file
    :return: "minor" or "adult"
    """
    # Load the image
    image = Image.open(image_path)

    # Transform the image and pass it through the model
    inputs = transforms(image, return_tensors='pt')
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
