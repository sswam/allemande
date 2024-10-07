#!/usr/bin/env python3
""" image-apply-masks: Apply masks to an image and save the masked images to a folder. """

import os
import argh
from argh import arg
from pathlib import Path
from PIL import Image
import numpy as np

def apply_mask(image, mask, invert=False):
	if invert:
		mask = Image.fromarray(255 - np.array(mask))
	masked_image = Image.composite(image, Image.new("RGBA", image.size, (0, 0, 0, 0)), mask)
	return masked_image

@arg("image_path", help="Path to the original image file")
@arg("mask_folder", help="Path to the folder containing mask images")
@arg("output_folder", help="Path to the folder where masked images will be saved")
def process_image(image_path: str, mask_folder: str, output_folder: str, invert=False):
	image = Image.open(image_path).convert("RGBA")
	mask_files = [f for f in os.listdir(mask_folder) if f.endswith(".png") or f.endswith(".jpg") or f.endswith(".jpeg")]

	output_path = Path(output_folder)
	output_path.mkdir(parents=True, exist_ok=True)

	for mask_file in mask_files:
		mask = Image.open(os.path.join(mask_folder, mask_file)).convert("L")
		masked_image = apply_mask(image, mask, invert)
		output_filename = os.path.splitext(mask_file)[0] + "_masked.png"
		masked_image.save(str(output_path / output_filename), format="PNG")

	print(f"Processed {len(mask_files)} masks and saved masked images to {output_folder}")

if __name__ == "__main__":
	argh.dispatch_command(process_image)
