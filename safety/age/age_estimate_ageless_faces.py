#!/usr/bin/env python3

"""
Estimates the age of individuals in images using the Ageless Faces model.
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
    model = transformers.ViTForImageClassification.from_pretrained('smarthat/ageless-faces')
    transforms = transformers.ViTImageProcessor.from_pretrained('smarthat/ageless-faces')


def estimate_age(image_path: str) -> str:
    """
    Estimates the age of an individual in the given image.
    :param image_path: Path to the image file
    :return: Age estimation as returned by the model
    """
    # Load the image
    image = Image.open(image_path)

    # Transform the image and pass it through the model
    inputs = transforms(images=image, return_tensors='pt')
    output = model(**inputs)

    # Get the predicted class probabilities and class labels
    # Since age prediction from this model is not strictly categorical, we'll use logits directly.
    logits = output.logits
    age_prediction = logits.item()

    # Return the prediction
    return f"{age_prediction}"


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

# Below is the script `age_estimate_ageless_faces.py` that uses the Ageless Faces model from Hugging Face to estimate the age of individuals in images. The script follows the same structure and code style as the provided example.

# **Note**: Ensure you have the necessary dependencies installed, including `transformers`, `PIL`, and any additional packages required by your `ally` module. The model `smarthat/ageless-faces` is used, which should be replaced if the actual model name differs. This script assumes that the model returns a continuous value for age estimation. Adjustments might be necessary based on the specific model's output format.
#
# **Important**: The model's handling and processing might vary based on the specifics of the model architecture and the framework version you are using. Always ensure you are using the correct and latest version of the model and its pre-processing logic.

