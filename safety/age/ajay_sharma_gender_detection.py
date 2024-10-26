#!/usr/bin/env python3

"""
Detects gender and age of individuals in images using AjaySharma/genderDetection.
"""

import sys
import logging
from typing import IO, TextIO
import cv2
import argparse
import numpy as np

from ally import main, logs

__version__ = "0.1.0"

logger = logs.get_logger()

# Model paths
face_detector_pbtxt_path = 'opencv_face_detector.pbtxt'
face_detector_pb_path = 'opencv_face_detector_uint8.pb'
age_deploy_path = 'age_deploy.prototxt'
age_net_path = 'age_net.caffemodel'
gender_deploy_path = 'gender_deploy.prototxt'
gender_net_path = 'gender_net.caffemodel'


def load_models():
    """Load the face detector, age detector, and gender detector models."""
    global face_detector, age_net, gender_net

    # Load face detector model
    face_detector = cv2.dnn.readNetFromCaffe(face_detector_pbtxt_path, face_detector_pb_path)

    # Load age detection model
    age_net = cv2.dnn.readNetFromCaffe(age_deploy_path, age_net_path)
    age_list = ['(0 - 2)', '(4 - 6)', '(8 - 12)', '(15 - 20)', '(25 - 32)', '(38 - 43)', '(48 - 53)', '(60 - 100)']
    age_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)

    # Load gender detection model
    gender_net = cv2.dnn.readNetFromCaffe(gender_deploy_path, gender_net_path)
    gender_list = ['Male', 'Female']
    gender_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_DEFAULT)


def detect_gender_age(image_path):
    """Detects gender and age from an image."""
    try:
        # Load the image
        img = cv2.imread(image_path)

        # Get the face locations
        face_locations = detect_faces(img, face_detector)

        if not face_locations:
            return "No Face Detected\tNo Age Detected\t" + image_path

        # Detect gender and age
        for (x, y, w, h) in face_locations:
            blob = cv2.dnn.blobFromImage(img[y:y+h, x:x+w], 1, (227, 227), (78.4263377603, 87.7689143744, 114.895847746), swapRB=False)
            gender_net.setInput(blob)
            gender_preds = gender_net.forward()
            gender = "Male" if np.argmax(gender_preds) == 0 else "Female"

            age_net.setInput(blob)
            age_preds = age_net.forward()
            age = age_list[np.argmax(age_preds)]
            return f"{gender}\t{age}\t{image_path}"

    except Exception as e:
        logger.error(f"Error processing image {image_path}: {e}")
        return f"Error\tError\t{image_path}"


def detect_faces(image, face_detector):
    """Detects faces in the given image."""
    (h, w) = image.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(image, (300, 300)), 1.0, (300, 300), (104.0, 177.0, 123.0))
    face_detector.setInput(blob)
    detections = face_detector.forward()

    face_locations = []
    for i in range(0, detections.shape):
        confidence = detections[0, 0, i, 2]
        if confidence < 0.5:
            continue
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (startX, startY, endX, endY) = box.astype("int")
        face_locations.append((startX, startY, endX - startX, endY - startY))

    return face_locations


def process_images(istream: TextIO, ostream: TextIO) -> None:
    """Processes images and detects gender and age from stdin to stdout."""
    load_models()
    for line in istream:
        image_path = line.strip()
        if not image_path or image_path.startswith('#'):
            continue
        prediction = detect_gender_age(image_path)
        ostream.write(f"{prediction}\n")


def setup_args(arg):
    """Setup the arguments for the script."""
    return arg


if __name__ == '__main__':
    main.go(process_images, setup_args)

# The script `ajay_sharma_gender_detection.py` uses AjaySharma/genderDetection from Hugging Face to detect gender and age from images. Note that AjaySharma/genderDetection is not a Hugging Face model but a repository containing code and pre-trained models for gender and age detection. The script below follows the style and structure of the provided example script.

# **Important Note:** Make sure you download the necessary model files (`opencv_face_detector.pbtxt`, `opencv_face_detector_uint8.pb`, `age_deploy.prototxt`, `age_net.caffemodel`, `gender_deploy.prototxt`, `gender_net.caffemodel`) and keep them in the same directory as your script, or update the paths in the script to match where you have stored these files.
#
# Also, ensure that your environment is set up with necessary dependencies (e.g., `cv2`, `numpy`, and any other required modules) for this script to run correctly.

