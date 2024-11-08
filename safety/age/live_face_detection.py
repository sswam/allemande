#!/usr/bin/env python3-allemande

import sys
import logging
from typing import IO, TextIO
import cv2
from io import BytesIO
import numpy as np

from ally import main, logs

__version__ = "0.1.0"

logger = logs.get_logger()

faceDetector = None
emotionModel = None
ageModel = None
genderModel = None

# Assuming these models are part of the project and need to be downloaded
# Replace with actual model file paths after downloading
FACE_DETECTOR_PATH = 'haarcascade_frontalface_default.xml'
EMOTION_MODEL_PATH = 'emotion_model.h5'
AGE_MODEL_PATH = 'age_modelprototxt.txt'
GENDER_MODEL_PATH = 'gender_modelprototxt.txt'

def load_models():
    """Initialize the models."""
    global faceDetector, emotionModel, ageModel, genderModel
    faceDetector = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    # Load the emotion, age, and gender models; adjust paths as necessary
    emotionModel = cv2.dnn.readNetFromCaffe("deploy.prototxt", EMOTION_MODEL_PATH)
    ageModel = cv2.dnn.readNetFromCaffe("deploy_age.prototxt", AGE_MODEL_PATH)
    genderModel = cv2.dnn.readNetFromCaffe("deploy_gender.prototxt", GENDER_MODEL_PATH)

def process_image(image_path: str) -> str:
    """
    Detects faces in the given image and estimates the age, gender, and emotion.
    :param image_path: Path to the image file
    :return: Output string in TSV format
    """
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = faceDetector.detectMultiScale(gray, 1.1, 5)

    output = ""
    for (x, y, w, h) in faces:
        face = gray[y:y+h, x:x+w]
        # Emotion detection
        blob = cv2.dnn.blobFromImage(face, 1, (48, 48), (0, 0, 0), True, False)
        emotionModel.setInput(blob)
        emotions = emotionModel.forward()
        emotionId = emotions.argmax()
        # Age detection
        blob = cv2.dnn.blobFromImage(face, 1, (227, 227), (0, 0, 0), True, False)
        ageModel.setInput(blob)
        age = ageModel.forward()
        # Gender detection
        genderModel.setInput(blob)
        gender = genderModel.forward()

        # Compile output
        output += f"{emotionId}\t{age}\t{gender}\t{image_path}\n"
    return output.strip()

def process_images(istream: TextIO, ostream: TextIO) -> None:
    """Processes images from stdin to stdout."""
    load_models()
    for line in istream:
        image_path = line.strip()
        if not image_path or image_path.startswith('#'):
            continue
        output = process_image(image_path)
        ostream.write(output + "\n")

def setup_args(arg):
    """Setup the arguments for the script."""


if __name__ == '__main__':
    main.go(process_images, setup_args)

# To write `live_face_detection.py` using the Dhrumit1314/Live_Face_Detection model from Hugging Face, you first need to download the necessary models and modify their paths in the script. However, since the model provided doesn't have a direct API for age detection and other specific attributes via Hugging Face's Transformers library (unlike the example script using Civitai/age-vit), we'll use OpenCV and the pre-trained face detection model to detect faces and predict emotions, age, and gender, as suggested in the model's documentation.
#
# Below is a simplified version of how you can process images using OpenCV for face detection and age/gender prediction. Unfortunately, the Dhrumit1314/Live_Face_Detection model doesn't directly support loading via the Hugging Face `transformers` library, so we need to focus on using OpenCV and similar techniques as presented in the model's documentation:

# **Note:**
#
# - This script assumes you have OpenCV installed.
# - You need to download and adjust the paths for the face detector, emotion, age, and gender models. The example uses placeholder paths (`EMOTION_MODEL_PATH`, `AGE_MODEL_PATH`, `GENDER_MODEL_PATH`) that you need to replace with actual model file paths after downloading.
# - The emotion, age, and gender models are placeholders and should be replaced with actual model files or paths.
# - The script uses a simplified approach to demonstrate how you can process images. You might need to adjust it based on the actual requirements and the specific models you use.
# - The Dhrumit1314/Live_Face_Detection model documentation provides more details on how to integrate and use the models with OpenCV. This script is a starting point and may need modifications to fit your exact needs.

