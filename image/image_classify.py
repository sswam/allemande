#!/usr/bin/env python3

"""Image classification using fastai model with optional fine-tuning capabilities"""

import argparse
import multiprocessing
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path

import torch
from fastai.vision.learner import load_learner
from fastai.vision.core import DataLoaders

nproc = multiprocessing.cpu_count()

import argparse
import multiprocessing
import shutil
import sys
from contextlib import redirect_stdout
from pathlib import Path

import torch
from fastai.vision.learner import load_learner
from fastai.vision.core import DataLoaders

nproc = multiprocessing.cpu_count()


def predict_one_at_time(learn) -> None:
    """Process individual images one at a time

    Args:
        learn: Loaded fastai learner model
    """
    for filename in sys.stdin:
        filename = filename.rstrip()
        pred, i, probs = learn.predict(filename)
        print(f"{probs[i]:.10f}\t{pred}\t{filename}", file=out)


def predict_in_batches(learn) -> None:
    """Process images in batches for better performance

    Args:
        learn: Loaded fastai learner model
    """
    if args.verbose:
        print(f"batch size {args.batch}", file=sys.stderr)
    batch = []
    for filename in sys.stdin:
        filename = filename.rstrip()
        batch.append(filename)
        if len(batch) >= args.batch:
            predict_batch(learn, batch)
            batch = []
    if batch:  # Process remaining images
        predict_batch(learn, batch)


def predict_batch(learn, batch: list[str]) -> None:
    """Make predictions on a batch of images

    Args:
        learn: Loaded fastai learner model
        batch: List of image filenames to process
    """
    vocab = learn.dls.vocab
    with redirect_stdout(sys.stderr):
        dl = learn.dls.test_dl(batch, num_workers=min(args.workers, args.batch))
        preds_all = learn.get_preds(dl=dl)

    for i, filename in enumerate(batch):
        preds = preds_all[0][i]
        pred_idx = preds.argmax(dim=0)
        label = vocab[pred_idx]
        prob = preds[pred_idx]
        print(f"{prob:.10f}\t{label}\t{filename}", file=out)

        if args.move is not None and prob >= args.move:
            Path(label).mkdir(exist_ok=True)
            shutil.move(filename, label)


def main() -> None:
    """Main entry point handling argument parsing and model loading"""
    global args, out

    out = sys.stdout

    parser = argparse.ArgumentParser(
        description="Classify images with a trained neural network.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="debug")
    parser.add_argument("--path", type=str, default=".", help="path to model")
    parser.add_argument("--model", type=str, default="export.pkl", help="model")
    parser.add_argument("--cpu", action="store_true", help="run on cpu")
    parser.add_argument("--batch", type=int, default=1, help="batch size")  # Changed default to 1
    parser.add_argument("--move", type=float, help="move files with certainty above the threshold")
    parser.add_argument(
        "--workers", type=int, default=nproc, help="max number of data loader workers"
    )
    parser.add_argument("--train", action="store_true", help="enable training mode")
    parser.add_argument("--lr", type=float, default=1e-4, help="learning rate")
    parser.add_argument(
        "--train-thresh",
        type=float,
        default=0.9,
        help="skip training on images classified above this confidence",
    )

    args = parser.parse_args()

    if args.verbose:
        print(torch.cuda.get_device_name(0), file=sys.stderr)

    model_path = Path(args.path) / Path(args.model)
    if not model_path.exists():
        model_path = Path.home() / Path(args.model)

    if args.verbose:
        print(model_path, file=sys.stderr)

    learn = load_learner(model_path)
    if args.cpu:
        torch.set_num_threads(nproc)
    else:
        try:
            learn.dls.to("cuda")
        except RuntimeError as e:
            print(f"CUDA error: {e}", file=sys.stderr)
            print("Falling back to CPU", file=sys.stderr)
            args.cpu = True
            torch.set_num_threads(nproc)

    if args.verbose:
        print(f"{learn.dls.device=}", file=sys.stderr)

    if args.batch == 1:
        predict_one_at_time(learn)
    else:
        predict_in_batches(learn)


if __name__ == "__main__":
    main()

# TODO: Use ally.main,logs,geput and ally.main.go
# TODO: the --move and --train-thresh options can be combined into one -c --confidence option (or a better name)
# TODO: --move should become a boolean option, off by default, whether to move confidently classified images or not
# TODO: I don't see a default for --workers, maybe it should default to nproc?
#
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
