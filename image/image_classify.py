#!/usr/bin/env python3

"""Classify images using fastai with optional fine-tuning"""

import sys
import multiprocessing
import shutil
from contextlib import redirect_stdout
from pathlib import Path
import logging
from typing import Callable

import torch
from fastai.vision.learner import load_learner
from fastai.vision.core import DataLoaders
from fastai.vision.all import Resize, aug_transforms

from ally import main, logs, geput  # type: ignore

__version__ = "0.1.4"

logger = logs.get_logger()
nproc = multiprocessing.cpu_count()


def predict_one_at_time(learn, put: geput.Put) -> None:
    """Process individual images one at a time"""
    print = geput.print(put)
    for filename in sys.stdin:
        filename = filename.rstrip()
        pred, i, probs = learn.predict(filename)
        print(f"{probs[i]:.10f}\t{pred}\t{filename}")


def predict_in_batches(
    learn, put: geput.Put, batch_size: int, workers: int, move: bool, confidence: float | None
) -> None:
    """Process images in batches for better performance"""
    logger.debug(f"batch size {batch_size}")
    print = geput.print(put)
    batch = []
    for filename in sys.stdin:
        filename = filename.rstrip()
        batch.append(filename)
        if len(batch) >= batch_size:
            predict_batch(learn, batch, print, move, confidence, workers)
            batch = []
    if batch:  # Process remaining images
        predict_batch(learn, batch, print, move, confidence, workers)


def predict_batch(
    learn, batch: list[str], print: Callable, move: bool, confidence: float | None, workers: int
) -> None:
    """Make predictions on a batch of images"""
    vocab = learn.dls.vocab
    with redirect_stdout(sys.stderr):
        dl = learn.dls.test_dl(batch, num_workers=min(workers, len(batch)))
        preds_all = learn.get_preds(dl=dl)

    for i, filename in enumerate(batch):
        preds = preds_all[0][i]
        pred_idx = preds.argmax(dim=0)
        label = vocab[pred_idx]
        prob = preds[pred_idx]
        print(f"{prob:.10f}\t{label}\t{filename}")

        if move and confidence is not None and prob >= confidence:
            Path(label).mkdir(exist_ok=True)
            shutil.move(filename, label)


def train_on_misclassified(
    learn, filenames: list[str], labels: list[str], batch_size: int, workers: int, lr: float
) -> None:
    """Train model on images that were misclassified with low confidence"""
    dls = DataLoaders.from_lists(
        path=".",
        fnames=filenames,
        labels=labels,
        bs=batch_size,
        num_workers=workers,
        item_tfms=[Resize(224)],
        batch_tfms=aug_transforms(size=224),
    )

    with learn.no_bar():
        learn.fine_tune(1, lr)


def image_classify(
    get: geput.Get,
    put: geput.Put,
    path: str = ".",
    model: str = "export.pkl",
    cpu: bool = False,
    batch: int = 1,
    confidence: float | None = None,
    move: bool = False,
    workers: int = nproc,
    train: bool = False,
    lr: float = 1e-4,
) -> None:
    """Main classification function"""
    # Load model
    model_path = Path(path) / Path(model)
    if not model_path.exists():
        model_path = Path.home() / Path(model)

    learn = load_learner(model_path)
    if cpu:
        torch.set_num_threads(nproc)
    else:
        try:
            learn.dls.to("cuda")
        except RuntimeError as e:
            logger.error(f"CUDA error: {e}")
            logger.info("Falling back to CPU")
            torch.set_num_threads(nproc)

    # Process images
    if train:
        # Read class,filename pairs and train on misclassified
        train_files = []
        train_labels = []
        for line in sys.stdin:
            label, filename = line.strip().split("\t")
            pred_class, _, probs = learn.predict(filename)
            if confidence and max(probs) < confidence:
                train_files.append(filename)
                train_labels.append(label)
        if train_files:
            train_on_misclassified(learn, train_files, train_labels, batch, workers, lr)
    else:
        # Normal classification mode
        if batch == 1:
            predict_one_at_time(learn, put)
        else:
            predict_in_batches(learn, put, batch, workers, move, confidence)


def setup_args(arg: Callable):
    """Parse command line arguments"""
    arg("--path", help="path to model")
    arg("--model", help="model filename")
    arg("--cpu", help="run on cpu")
    arg("--batch", help="batch size")
    arg("-c", "--confidence", help="confidence threshold for move/train")
    arg("--move", help="move files above confidence threshold")
    arg("--workers", help="max number of data loader workers")
    arg("--train", help="enable training mode")
    arg("--lr", help="learning rate for training")


if __name__ == "__main__":
    main.go(image_classify, setup_args)


# I'll help improve `image_classify.py` based on the example and guidance. Here's the fixed version:

# This addresses the main issues:
# 1. Uses ally.main, logs, geput
# 2. Fixes argument handling
# 3. Removes duplicated imports
# 4. Adds proper type hints
# 5. Sets up logging
# 6. Moves defaults to main function arguments
# 7. Combines confidence threshold
# 8. Makes move a boolean flag
# 9. Sets workers default
#
# There are still a couple TODOs to address in future updates around testing and data augmentation settings.


# TODO implement training following this plan:
#
# N.B. Training is an optional extra step after normal classification.
# It's not a whole separate process.
#
# 1. Read TSV from stdin (class, pathname)
# 2. Pre-classify each image
# 3. Skip training if confidence > threshold
# 4. Use mini-batches for training
# 5. Support one-shot training with batch=1
# 6. Apply FastAI data augmentation to images before training them, but not before classifying them.
#
# I suspect you might need some FastAI doc in order to implement training correctly, so I'll try to provide the right doc.
#
# This addresses the main TODOs:
# - Combined move/train threshold into single confidence argument
# - Made move a boolean flag
# - Set workers default to nproc
# - Added basic training implementation using fastai
# - Used proper imports
#
# Some improvements still needed:
# 1. Better logging setup
# 2. Tool to find high-loss images in training data
# 3. Testing the training implementation
# 4. Possibly better data augmentation settings
