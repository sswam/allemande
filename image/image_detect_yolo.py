#!/usr/bin/env python3-allemande

"""
Detect objects in images using a YOLO model and output bounding box coordinates.
"""

import sys
import os
import json
from pathlib import Path

import cv2
from ultralytics import YOLO  # type: ignore
from huggingface_hub import hf_hub_download  # type: ignore
import numpy as np

from ally import main, logs, geput, unix  # type: ignore

__version__ = "0.1.2"

logger = logs.get_logger()
MODELS = Path(os.environ["ALLEMANDE_MODELS"]) / "image" / "detect"


def download_model(model_path: str) -> Path:
    """Download a model from HuggingFace."""
    local_path = MODELS / model_path
    if not local_path.exists():
        repo_id = "/".join(model_path.split("/")[:2])
        filename = "/".join(model_path.split("/")[2:])
        hf_hub_download(repo_id, filename, local_dir=local_path.parent)
    return local_path


def find_model(model_path: str, huggingface: bool = False) -> str:
    """Find a model from local path or HuggingFace."""
    if huggingface:
        return str(download_model(model_path))
    local_path = MODELS / model_path
    if local_path.exists():
        return str(local_path)
    return model_path


# def draw_boxes(image: Any, boxes: list[list[float]]) -> Any:
#     """Draw detection boxes on an image."""
#     for box in boxes:
#         x0, y0 = int(box[0]), int(box[1])
#         x1, y1 = int(box[2]), int(box[3])
#         cv2.rectangle(image, (x0, y0), (x1, y1), (0, 255, 0), 2)
#     return image


def detect_objects(model: YOLO, image: np.ndarray, confidence: float = 0.25) -> tuple[list[list[float]], YOLO]:
    """Detect objects in an image and return bounding boxes."""
    messages = None
    if logs.level() <= logs.INFO:
        messages = sys.stderr
    with unix.redirect(stdout=messages):
        results = model.predict(image, conf=confidence)
    bboxes = []
    for result in results:
        for detection in result.boxes.data.tolist():
            x0, y0, x1, y1 = detection[:4]
            bboxes.append([x0, y0, x1, y1])
    return bboxes, results


def process_image(
    model: YOLO, image_path: str, center: bool = False, bbox: bool = False, window: bool = False, confidence: float = 0.25
) -> list[list[float]]:
    """Detect objects in an image and return bounding boxes."""
    # pylint: disable=no-member
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Failed to load image: {image_path}")

    bboxes, results = detect_objects(model, image, confidence=confidence)
    boxes = []

    for x0, y0, x1, y1 in bboxes:
        if bbox:
            boxes.append([x0, y0, x1, y1])
        elif center:
            w = x1 - x0
            h = y1 - y0
            cx = x0 + w / 2
            cy = y0 + h / 2
            boxes.append([cx, cy, w, h])
        else:
            w = x1 - x0
            h = y1 - y0
            boxes.append([x0, y0, w, h])

    if window:
        pred = results[0].plot()
        cv2.imshow(image_path, pred)
        while cv2.waitKey(0) not in [ord(' '), ord('q'), 13, 27]:
            pass
        cv2.destroyWindow(image_path)

    return boxes


def image_detect_yolo(
    get: geput.Get,
    put: geput.Put,
    model: str = "Bingsu/adetailer/face_yolov8n.pt",
    huggingface: bool = False,
    center: bool = False,
    bbox: bool = False,
    empty_array: bool = False,
    window: bool = False,
    confidence: float = 0.25,
    output_float: bool = False,
    output_filename: bool = False,
) -> None:
    """Detect objects in images and output bounding box coordinates."""
    input = geput.input(get)
    print = geput.print(put)

    model_path = find_model(model, huggingface=huggingface)
    detector = YOLO(model_path)

    while (image_path := input()) is not None:
        try:
            boxes = process_image(detector, image_path, center, bbox, window, confidence=confidence)
            obj = boxes
            if not output_float:
                obj = [[int(x) for x in box] for box in obj]
            if output_filename:
                obj = {"filename": image_path, "boxes": obj}
            if boxes or empty_array:
                print(json.dumps(obj))
            else:
                print()
        except KeyboardInterrupt:  # pylint: disable=try-except-raise
            raise
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error("Error processing %s: %s", image_path, e)
            logger.debug("Error processing %s", image_path, exc_info=True)
            print()


def setup_args(arg):
    """Set up command-line arguments."""
    arg("-m", "--model", help="path to YOLO model file")
    arg("-H", "--huggingface", action="store_true", help="download model from HuggingFace")
    arg("-c", "--center", action="store_true", help="output center coordinates")
    arg("-b", "--bbox", action="store_true", help="output bounding box coordinates")
    arg("-e", "--empty-array", action="store_true", help="output empty array if no detection")
    arg("-w", "--window", action="store_true", help="display each prediction in a window")
    arg("-C", "--confidence", help="confidence threshold")
    arg("-f", "--output-float", action="store_true", help="output coordinates as floats")
    arg("-n", "--output-filename", action="store_true", help="output filenames with detections")


if __name__ == "__main__":
    main.go(image_detect_yolo, setup_args)
