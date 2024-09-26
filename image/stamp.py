#!/usr/bin/env python3

"""
Process image comment metadata, such as AI image generation parameters
"""

import sys
import subprocess
from typing import Optional
from pathlib import Path

from argh import arg
from ally import main

__version__ = "0.1.1"

logger = main.get_logger()


def extract_metadata(input_file: Path) -> str:
	"""Extract metadata from an image."""
	if input_file.suffix.lower() == ".png":
		result = subprocess.run(
			["magick", "identify", "-format", "%[Property:parameters]", str(input_file)],
			capture_output=True,
			text=True,
		)
		return result.stdout.strip()
	elif input_file.suffix.lower() in (".jpg", ".jpeg", ".tif", ".tiff", ".webp"):
		result = subprocess.run(
			["exiftool", "-UserComment", "-b", str(input_file)],
			capture_output=True,
			text=True,
		)
		return result.stdout.strip()
	else:
		raise ValueError("Unsupported file format")


def insert_metadata(input_file: Path, metadata: str, output_file: Path) -> None:
	"""Insert metadata into an image."""
	if input_file.suffix.lower() == ".png":
		subprocess.run(
			["magick", "convert", str(input_file), "-set", "parameters", metadata, str(output_file)],
			check=True,
		)
	elif input_file.suffix.lower() in (".jpg", ".jpeg", ".tif", ".tiff", ".webp"):
		subprocess.run(
			["exiftool", "-overwrite_original", "-preserve", f"-UserComment={metadata}", str(output_file)],
			check=True,
			capture_output=True,
		)
	else:
		raise ValueError("Unsupported file format")


def erase_metadata(input_file: Path, output_file: Path) -> None:
	"""Erase metadata from an image."""
	if input_file.suffix.lower() == ".png":
		subprocess.run(
			["magick", "convert", str(input_file), "-set", "parameters", "", str(output_file)],
			check=True,
		)
	elif input_file.suffix.lower() in (".jpg", ".jpeg", ".tif", ".tiff", ".webp"):
		subprocess.run(
			["exiftool", "-overwrite_original", "-preserve", "-UserComment=", str(output_file)],
			check=True,
			capture_output=True,
		)
	else:
		raise ValueError("Unsupported file format")


def convert_image(input_file: Path, output_file: Path, quality: int = 95) -> None:
	"""Convert image format and copy metadata."""
	subprocess.run(
		["magick", "convert", str(input_file), "-quality", str(quality), str(output_file)],
		check=True,
	)
	metadata = extract_metadata(input_file)
	if metadata:
		insert_metadata(output_file, metadata, output_file)


@arg("action", choices=["get", "set", "rm", "cp", "convert"], help="Action to perform")
@arg("image", help="image file")
@arg("-o", "--output", help="Output file")
@arg("-m", "--metadata", help="Metadata file or string for 'set' action")
@arg("-q", "--quality", type=int, default=95, help="JPEG quality for 'convert' action")
def stamp(
	action: str,
	image: str,
	output: Optional[str] = None,
	metadata: Optional[str] = None,
	quality: int = 95,
) -> None:
	"""Process image comment metadata."""
	input_file = Path(image)
	output_file = Path(output) if output else None

	if action == "get":
		metadata = extract_metadata(input_file)
		print(metadata)
	elif action == "set":
		if not metadata:
			raise ValueError("Metadata is required for 'set' action")
		if Path(metadata).is_file():
			metadata = Path(metadata).read_text().strip()
		output_file = output_file or input_file
		insert_metadata(input_file, metadata, output_file)
	elif action == "rm":
		output_file = output_file or input_file
		erase_metadata(input_file, output_file)
	elif action == "cp":
		if not output_file:
			raise ValueError("Output file is required for 'cp' action")
		metadata = extract_metadata(input_file)
		insert_metadata(output_file, metadata, output_file)
	elif action == "convert":
		if not output_file:
			raise ValueError("Output file is required for 'convert' action")
		convert_image(input_file, output_file, quality)
	else:
		raise ValueError(f"Unknown action: {action}")

	logger.info(f"Action '{action}' completed successfully")


if __name__ == "__main__":
	main.run(stamp)
