#!/usr/bin/env python3-allemande

"""
Process image comment metadata, such as AI image generation parameters
"""

import sys
import subprocess
from typing import Optional
from pathlib import Path

from argh import arg
from ally import main  # type: ignore

__version__ = "0.1.3"

logger = main.get_logger()


USE_MAGICK_EXT = {"png"}
USE_EXIFTOOL_EXT = {"jpg", "jpeg", "tif", "tiff", "webp"}


def check_extention(file: Path, exts: set[str]) -> bool:
    """Check if file has one of the given extensions."""
    ext = file.suffix.lower()
    if ext.startswith("."):
        ext = ext[1:]
    return ext in exts


def extract_metadata(input_file: Path) -> str:
    """Extract metadata from an image."""
    if check_extention(input_file, USE_MAGICK_EXT):
        result = subprocess.run(
            ["magick", "identify", "-format", "%[Property:parameters]", str(input_file)],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    elif check_extention(input_file, USE_EXIFTOOL_EXT):
        result = subprocess.run(
            ["exiftool", "-UserComment", "-b", str(input_file)],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    else:
        raise ValueError("Unsupported file format")


def insert_metadata(input_file: Path, metadata: str, output_file: Path) -> None:
    """Insert metadata into an image."""
    if check_extention(input_file, USE_MAGICK_EXT):
        subprocess.run(
            [
                "magick",
                "convert",
                str(input_file),
                "-set",
                "parameters",
                metadata,
                str(output_file),
            ],
            check=True,
        )
    elif check_extention(input_file, USE_EXIFTOOL_EXT):
        subprocess.run(
            [
                "exiftool",
                "-overwrite_original",
                "-preserve",
                f"-UserComment={metadata}",
                str(output_file),
            ],
            check=True,
            capture_output=True,
        )
    else:
        raise ValueError("Unsupported file format")


def erase_metadata(input_file: Path, output_file: Path) -> None:
    """Erase metadata from an image."""
    if check_extention(input_file, USE_MAGICK_EXT):
        subprocess.run(
            ["magick", "convert", str(input_file), "-set", "parameters", "", str(output_file)],
            check=True,
        )
    elif check_extention(input_file, USE_EXIFTOOL_EXT):
        subprocess.run(
            ["exiftool", "-overwrite_original", "-preserve", "-UserComment=", str(output_file)],
            check=True,
            capture_output=True,
        )
    else:
        raise ValueError("Unsupported file format")


def extract_comfy_metadata(input_file: Path) -> tuple[str, str]:
    """Extract ComfyUI metadata from Make and Model fields."""
    result = subprocess.run(
        ["exiftool", "-Make", "-Model", "-b", str(input_file)],
        capture_output=True,
        text=True,
        check=True,
    )
    workflow = ""
    prompt = ""
    for line in result.stdout.splitlines():
        if line.startswith("workflow:"):
            workflow = line[9:]
        elif line.startswith("prompt:"):
            prompt = line[7:]
    return workflow, prompt


def insert_comfy_metadata(input_file: Path, workflow: str, prompt: str, output_file: Path) -> None:
    """Insert ComfyUI metadata into Make and Model fields."""
    subprocess.run(
        [
            "exiftool",
            "-overwrite_original",
            "-preserve",
            f"-Make=workflow:{workflow}",
            f"-Model=prompt:{prompt}",
            str(output_file),
        ],
        check=True,
        capture_output=True,
    )


def erase_comfy_metadata(input_file: Path, output_file: Path) -> None:
    """Erase ComfyUI metadata fields."""
    workflow, prompt = extract_comfy_metadata(input_file)
    if not (workflow.startswith("workflow:") or prompt.startswith("prompt:")):
        return  # Don't erase if not ComfyUI metadata
    subprocess.run(
        [
            "exiftool",
            "-overwrite_original",
            "-preserve",
            "-Make=",
            "-Model=",
            str(output_file),
        ],
        check=True,
        capture_output=True,
    )


def convert_image(input_file: Path, output_file: Path, quality: int = 95) -> None:
    """Convert image format and copy metadata."""
    subprocess.run(
        ["magick", "convert", str(input_file), "-quality", str(quality), str(output_file)],
        check=True,
    )
    metadata = extract_metadata(input_file)
    if metadata:
        insert_metadata(output_file, metadata, output_file)


def parse_comfy_metadata(metadata: str) -> tuple[str, str]:
    """Parse ComfyUI metadata."""
    workflow = ""
    prompt = ""
    def error():
        return ValueError("ComfyUI metadata lines must start with 'workflow:' or 'prompt:'")
    lines = metadata.strip().splitlines():
    for line in lines:
        try:
            key, value = line.split(":", 1)
        except ValueError:
            raise error()
        if key == "workflow":
            workflow = value
        elif key == "prompt":
            prompt = value
        else:
            raise error()
    return workflow, prompt


def format_comfy_metadata(workflow: str, prompt: str) -> str:
    """Format ComfyUI metadata."""
    return f"workflow:{workflow}\nprompt:{prompt}\n"


def stamp(
    action: str,
    image: str,
    output: Optional[str] = None,
    quality: int = 95,
    comfy: bool = False,
) -> None:
    """Process image comment metadata."""
    input_file = Path(image)
    output_file = Path(output) if output else None

    if action == "get":
        if comfy:
            workflow, prompt = extract_comfy_metadata(input_file)
            print(format_comfy_metadata(workflow, prompt))
        else:
            metadata = extract_metadata(input_file)
            print(metadata)
    elif action == "set":
        if comfy:
            workflow, prompt = parse_comfy_metadata(sys.stdin.read())
            output_file = output_file or input_file
            insert_comfy_metadata(input_file, workflow, prompt, output_file)
        else:
            metadata = sys.stdin.read().strip()
            output_file = output_file or input_file
            insert_metadata(input_file, metadata, output_file)
    elif action == "rm":
        output_file = output_file or input_file
        if comfy:
            erase_comfy_metadata(input_file, output_file)
        else:
            erase_metadata(input_file, output_file)
    elif action == "cp":
        if not output_file:
            raise ValueError("Output file is required for 'cp' action")
        if comfy:
            workflow, prompt = extract_comfy_metadata(input_file)
            insert_comfy_metadata(output_file, workflow, prompt, output_file)
        else:
            metadata = extract_metadata(input_file)
            insert_metadata(output_file, metadata, output_file)
    elif action == "convert":
        if not output_file:
            raise ValueError("Output file is required for 'convert' action")
        convert_image(input_file, output_file, quality)
    else:
        raise ValueError(f"Unknown action: {action}")

    logger.info("Action '%s' completed successfully", action)


def setup_args(arg):
    arg("action", choices=["get", "set", "rm", "cp", "convert"], help="Action to perform")
    arg("image", help="image file")
    arg("-o", "--output", help="Output file")
    arg("-q", "--quality", type=int, default=95, help="JPEG quality for 'convert' action")
    arg("-c", "--comfy", help="Use ComfyUI metadata format")


if __name__ == "__main__":
    main.go(stamp, setup_args)

# TODO: need to be able to set ComfyUI metadata on png files with magick
# TODO: add tests for comfy metadata
# TODO: careful code review
