#!/usr/bin/env python3
import argparse
import csv
import os
import requests
import torch
from PIL import Image
from clip_interrogator import Interrogator, Config, list_clip_models
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def inference(ci, image, mode):
    image = image.convert('RGB')
    if mode == 'best':
        return ci.interrogate(image)
    elif mode == 'classic':
        return ci.interrogate_classic(image)
    else:
        return ci.interrogate_fast(image)

def main():
    parser = argparse.ArgumentParser(description='Generate text prompts from images', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--clip', default='ViT-L-14/openai', help='name of CLIP model to use')
    parser.add_argument('-d', '--device', default='auto', help='device to use (auto, cuda or cpu)')
    parser.add_argument('-f', '--folder', help='path to folder of images')
    parser.add_argument('-i', '--image', help='image file or url')
    parser.add_argument('-m', '--mode', default='best', help='best, classic, or fast')
    parser.add_argument("--lowvram", action='store_true', help="Optimize settings for low VRAM")
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')

    args = parser.parse_args()
    if not args.folder and not args.image:
        parser.print_help()
        exit(1)

    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(format="%(message)s", level=log_level)

    if args.folder is not None and args.image is not None:
        logger.error("Specify a folder or batch processing or a single image, not both")
        exit(1)

    # validate clip model name
    models = list_clip_models()
    if args.clip not in models:
        logger.error(f"Could not find CLIP model {args.clip}!")
        logger.error(f"    available models: {models}")

    # select device
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        if not torch.cuda.is_available():
            logger.warning("CUDA is not available, using CPU. Warning: this will be very slow!")
    else:
        device = torch.device(args.device)

    # generate a nice prompt
    cache_path = Path(os.environ.get("AI_MODELS", '/opt/models'))/"clip_interrogator"
    config = Config(device=device, clip_model_name=args.clip, cache_path=str(cache_path), quiet=not args.verbose)
    if args.lowvram:
        config.apply_low_vram_defaults()
    ci = Interrogator(config)

    # process single image
    if args.image is not None:
        image_path = args.image
        if str(image_path).startswith('http://') or str(image_path).startswith('https://'):
            image = Image.open(requests.get(image_path, stream=True).raw).convert('RGB')
        else:
            image = Image.open(image_path).convert('RGB')
        if not image:
            logger.error(f'Error opening image {image_path}')
            exit(1)
        print(inference(ci, image, args.mode))

    # process folder of images
    elif args.folder is not None:
        if not os.path.exists(args.folder):
            logger.error(f'The folder {args.folder} does not exist!')
            exit(1)

        files = [f for f in os.listdir(args.folder) if f.endswith('.jpg') or  f.endswith('.png')]
        prompts = []
        for file in files:
            image = Image.open(os.path.join(args.folder, file)).convert('RGB')
            prompt = inference(ci, image, args.mode)
            prompts.append(prompt)
            print(file, prompt, sep='\t')

        if len(prompts):
            csv_path = os.path.join(args.folder, 'desc.csv')
            with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                w = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
                w.writerow(['image', 'prompt'])
                for file, prompt in zip(files, prompts):
                    w.writerow([file, prompt])

            logger.info(f"\n\n\n\nGenerated {len(prompts)} and saved to {csv_path}, enjoy!")

if __name__ == "__main__":
    main()
