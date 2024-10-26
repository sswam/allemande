#!/usr/bin/env python3

"""
Estimates the age of individuals in images using the LisanneH/AgeEstimation model.
"""

import sys
import logging
from typing import IO, TextIO
from io import BytesIO
import torch

from PIL import Image
import requests
import transformers

from ally import main, logs

__version__ = "0.1.0"

logger = logs.get_logger()

model = None


def load_model():
    """Initialize the model."""
    global model
    # Note: LisanneH/AgeEstimation is a CNN model for age regression, not classification.
    # It returns a continuous age value, not class labels.
    model = torch.hub.load('LisanneH/AgeEstimation', 'AgeEstimation', pretrained=True)
    model.eval()


def estimate_age(image_path: str) -> str:
    """
    Estimates the age of an individual in the given image.
    :param image_path: Path to the image file
    :return: Estimated age as a string
    """
    # Load the image
    image = Image.open(image_path)

    # Preprocess the image
    # Note: The preprocessing steps are not explicitly provided in the model card.
    # However, based on the CNN architecture and the dataset description, it seems
    # that the images are resized to 224x224 and normalized using the ImageNet mean and std.
    image = image.resize((224, 224))
    image = transformers.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])(image)

    # Pass the image through the model
    output = model(image.unsqueeze(0))

    # Get the predicted age
    predicted_age = output.item()

    # Return the prediction
    return str(predicted_age)


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

# **age_estimate_lisanneh.py**

# This script uses the LisanneH/AgeEstimation model, which is a CNN model for age regression. It takes an image as input, preprocesses it, and passes it through the model to get the estimated age. The script reads image paths from stdin, one per line, and writes the estimated age and image path to stdout in TSV format.
#
# Note that the preprocessing steps are not explicitly provided in the model card, so I assumed that the images are resized to 224x224 and normalized using the ImageNet mean and std, which is a common practice for CNN models. If the actual preprocessing steps are different, you may need to modify the script accordingly.
#
# Also, I used `torch.hub.load` to load the model, as it is not available on the Hugging Face model hub. If you want to use the Hugging Face model hub, you can modify the script to use `transformers.AutoModel.from_pretrained` instead. However, this may require additional modifications to the script, as the model architecture and preprocessing steps may be different.

