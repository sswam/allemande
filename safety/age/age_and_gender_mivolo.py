#!/usr/bin/env python3

"""
Estimates the age and gender of individuals in images using the MiVOLO model.
"""

import sys
import os
import logging
import numpy as np
from typing import TextIO
from io import BytesIO
import gradio
import huggingface_hub
from PIL import Image
import torch

from ally import main, logs

__version__ = "0.1.0"

logger = logs.get_logger()

device = "cuda" if torch.cuda.is_available() else "cpu"

class MiVOLO:
    def __init__(self):
        self.detector_path = huggingface_hub.hf_hub_download('iitolstykh/demo_yolov8_detector', 'yolov8x_person_face.pt')
        self.age_gender_path = huggingface_hub.hf_hub_download('iitolstykh/demo_xnet_volo_cross', 'mivolo_v2_384_0.15.pth.tar')
        self.detector = torch.jit.load(self.detector_path, map_location=device)
        self.age_gender_model = torch.jit.load(self.age_gender_path, map_location=device)

    def estimate(self, image_path: str):
        """
        Estimates the age and gender of an individual in the given image.
        :param image_path: Path to the image file
        :return: Age (as a float) and gender (as "male" or "female")
        """
        # Load the image
        image = np.array(Image.open(image_path))
        image = image[:, :, ::-1]  # RGB -> BGR
        inputs = torch.tensor(image).permute(2, 0, 1).unsqueeze(0).float().to(device)

        # Run the detector to get person and face bounding boxes
        # Here, we assume the first bounding box is used. Adjust logic as necessary.
        outputs = self.detector(inputs)
        person_bbox = outputs['person_bboxes'] if len(outputs['person_bboxes']) > 0 else None
        face_bbox = outputs['face_bboxes'] if len(outputs['face_bboxes']) > 0 else None

        # Prepare inputs for age and gender estimation
        if person_bbox is not None:
            inputs_person = inputs[:, :, int(person_bbox):int(person_bbox), int(person_bbox):int(person_bbox)]
        else:
            inputs_person = None
        if face_bbox is not None:
            inputs_face = inputs[:, :, int(face_bbox):int(face_bbox), int(face_bbox):int(face_bbox)]
        else:
            inputs_face = None

        # Run the age and gender model
        if inputs_person is not None and inputs_face is not None:
            outputs = self.age_gender_model({'person': inputs_person, 'face': inputs_face})
        elif inputs_person is not None:
            outputs = self.age_gender_model({'person': inputs_person})
        elif inputs_face is not None:
            outputs = self.age_gender_model({'face': inputs_face})
        else:
            return "Could not detect person or face", "N/A", image_path

        # Interpret the results
        age = outputs['age'].item()
        gender = 'male' if outputs['gender'] > 0.5 else 'female'

        return str(age), gender, image_path

def process_images(istream: TextIO, ostream: TextIO) -> None:
    """Processes images and estimates ages and genders from stdin to stdout."""
    model = MiVOLO()
    for line in istream:
        image_path = line.strip()
        if not image_path or image_path.startswith('#'):
            continue
        age, gender, image_path = model.estimate(image_path)
        ostream.write(f"{age}\t{gender}\t{image_path}\n")

def setup_args(arg):
    """Setup the arguments for the script."""
    pass

if __name__ == '__main__':
    main.go(process_images, setup_args)

# Here is the script using MiVOLO for age and gender estimation based on the provided example:

# This script uses the `MiVOLO` model to estimate the age and gender of individuals in images provided on `stdin`, one path per line, and outputs the results to `stdout` in a tab-separated format, with the image path in the last column. The script assumes that the `ally` module is available for `main.go` and `logs.get_logger()` functions. If you need to adjust the input/output logic or the model's behavior, please modify the script accordingly. Ensure that you have the necessary Hugging Face Hub token environment variable set to access the model weights (`HF_TOKEN`).
#
# **Important Note**: The script above uses simplified input handling for demonstration purposes and may need adjustments for production use, especially regarding error handling and bounding box selection logic. Make sure to test it thoroughly before using it in critical applications.

