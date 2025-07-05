"""Module for handling image processing and encoding for vision-based language models."""

__VERSION__ = "0.1.10"


import base64
from urllib.parse import urlparse
from copy import deepcopy
import logging
from pathlib import Path
from typing import Any

from PIL import Image
from PIL.Image import Image as PILImage

from ally.lazy import lazy

# Lazy imports for API clients
lazy(
    "google.genai",
    _as="google_genai",
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def is_url(string: str) -> bool:
    """Check if a string is a valid URL."""
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def load_image_file(image_path: str) -> str:
    """Load an image file and return its binary content."""
    try:
        with open(image_path, "rb") as image_file:
            return image_file.read()
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Image file not found: {image_path}") from exc
    except OSError as exc:
        raise OSError(f"Error reading image file: {image_path}: {exc}") from exc


def encode_image_file(image_path: str) -> str:
    """Encode a local image file to base64."""
    return base64.b64encode(load_image_file(image_path)).decode("utf-8")


def calculate_resize_factor(
    width: int, height: int, max_pixels: int | None, max_short_side: int | None, max_long_side: int | None
) -> float:
    """
    Calculate resize factor based on max pixels and max side length constraints.

    Args:
        width: Original image width
        height: Original image height
        max_pixels: Maximum total pixels allowed
        max_short_side: Maximum length allowed for the shorter side
        max_long_side: Maximum length allowed for the longer side

    Returns:
        float: Resize factor to apply to both dimensions
    """
    # Determine short and long sides
    short_side = min(width, height)
    long_side = max(width, height)

    factors = []

    # Check short side constraint
    if max_short_side is not None and short_side > max_short_side:
        factors.append(max_short_side / short_side)

    # Check long side constraint
    if max_long_side is not None and long_side > max_long_side:
        factors.append(max_long_side / long_side)

    # Check total pixels constraint
    pixels = width * height
    if max_pixels is not None and pixels > max_pixels:
        factors.append((max_pixels / pixels) ** 0.5)

    # If any constraints were exceeded, return the smallest factor
    # (most restrictive constraint)
    if factors:
        return min(factors)

    # If no constraints were exceeded, return 1.0 (no resize needed)
    return 1.0


def process_image_if_needed(img: PILImage, detail: str = "auto", convert_to_rgb: bool = True) -> PILImage:
    """
    Resize and potentially convert image according to minimum vendor constraints.

    Args:
        img: Source image
        detail: Detail level for OpenAI ('auto', 'low', 'high')
        convert_to_rgb: Whether to convert to RGB colorspace if needed

    Returns:
        ResizeResult containing:
        - Processed image (or original if unchanged)
    """
    width, height = img.size
    processed_img = img

    # Handle color space conversion if needed
    if convert_to_rgb and img.mode not in ["RGB", "RGBA"]:
        processed_img = img.convert("RGB")

    # Use a common lower limit so we can share the cached resized images
    if detail == "low":
        factor = calculate_resize_factor(width, height, None, 512, 512)
    else:
        factor = calculate_resize_factor(width, height, 1150000, 768, 1568)

    # Resize if needed
    if factor < 1.0:
        new_width = int(width * factor + 1e-6)
        new_height = int(height * factor + 1e-6)
        processed_img = processed_img.resize((new_width, new_height), Image.Resampling.LANCZOS)

    return processed_img


def get_supported_image_mime_type(img: PILImage) -> tuple[str, bool]:
    """
    Get the MIME type of an image file and whether conversion is needed.
    Supports PNG, JPEG, WEBP, and non-animated GIF.
    Returns tuple of (mime_type, needs_conversion).
    Raises ValueError for invalid formats.
    """

    try:
        # Open image to verify it's a valid image file
        if img.format is None:
            raise ValueError("Invalid or unsupported image format")

        img_format = img.format.lower()

        # Handle each format
        if img_format == "png":
            return "image/png", False
        if img_format == "jpeg":
            return "image/jpeg", False
        if img_format == "webp":
            return "image/webp", True  # Convert WEBP
        if img_format == "gif":
            # Check if GIF is animated
            try:
                img.seek(1)
                return "image/gif", False
            except EOFError:
                # Not animated
                return "image/gif", True

        # Valid format but not supported - will convert
        return f"image/{img_format}", True

    except (IOError, OSError) as exc:
        raise ValueError(f"Invalid or corrupted image file: {exc}") from exc


def get_image_to_send(image_source: str, detail: str = "auto") -> tuple[Path, str]:
    """Get or create JPEG version of image, returning path and base64 encoding."""
    conv_type = "low" if detail == "low" else "high"
    converted_jpeg_path = Path(image_source).parent / f".{Path(image_source).name}.{conv_type}.jpg"

    # Use existing converted file if available
    if converted_jpeg_path.exists():
        return converted_jpeg_path, "image/jpeg"

    # Process image if needed
    try:
        with Image.open(image_source) as img:
            mime_type, needs_conversion = get_supported_image_mime_type(img)
            processed_img = process_image_if_needed(img, detail)

        if needs_conversion or processed_img is not img:
            # Save as JPEG alongside original
            processed_img.convert("RGB").save(converted_jpeg_path, "JPEG")
            return converted_jpeg_path, "image/jpeg"

        # Use original file if no conversion needed
        return Path(image_source), mime_type
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Could not find image at {image_source}") from e
    except Exception as e: # pylint: disable=broad-except
        raise Exception(f"An unexpected error occurred while processing the image: {e}") from e  # pylint: disable=broad-exception-raised


def format_image(image_source: str, vendor: str, detail: str = "auto") -> dict[str, Any]:
    """Format an image source into OpenAI's expected structure."""
    if is_url(image_source):
        if not image_source.startswith(("http://", "https://")):
            raise ValueError("Invalid URL format. URL must start with http:// or https://")
        if vendor == "openai":
            return {"type": "image_url", "image_url": {"url": image_source, "detail": detail}}
        if vendor == "anthropic":
            return {"type": "image", "source": {"type": "url", "url": image_source}}
        if vendor == "google":
            # TODO could download
            logger.error(f"Unsupported vendor for remote image: {vendor}")
            return None
        raise ValueError(f"Unsupported vendor: {vendor}")

    # For local files
    try:
        # Get JPEG version and encode
        file_path, mime_type = get_image_to_send(image_source, detail)

        if vendor == "openai":
            base64_image = encode_image_file(str(file_path))
            return {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}", "detail": detail}}
        if vendor == "anthropic":
            base64_image = encode_image_file(str(file_path))
            return {"type": "image", "source": {"type": "base64", "media_type": mime_type, "data": base64_image}}
        if vendor == "google":
            image_bytes = load_image_file(str(file_path))
            return google_genai.types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        raise ValueError(f"Unsupported vendor: {vendor}")
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Local file not found: {image_source}") from e
    except Exception as e: # pylint: disable=broad-except
        raise Exception(f"An unexpected error occurred while formatting the image: {e}") from e  # pylint: disable=broad-exception-raised


def handle_text_content(message: dict, content: list) -> list[dict]:
    """Handle text content for OpenAI and Anthropic."""
    if "content" not in message:
        return content

    text_content = message["content"]
    if isinstance(text_content, list):
        # content = text_content + content
        content = content + text_content
    elif isinstance(text_content, str):
        # content.insert(0, {"type": "text", "text": text_content})
        content.append({"type": "text", "text": text_content})
    else:
        raise ValueError(f"Unsupported content type: {type(text_content)}")
    return content


def format_message_for_vision(message: dict, vendor: str, detail: str = "auto") -> dict:
    """Base function for processing messages with images for LLMs."""
    # shortcut for messages with no images
    if not message.get("images"):
        message.pop("images", None)
        return message

    if vendor not in ["openai", "anthropic", "google"]:
        raise ValueError(f"Unsupported vendor: {vendor}")

    try:
        # Create a deep copy of the input message
        processed_message = deepcopy(message)

        # Get the image sources and remove the original image key
        image_sources = processed_message.pop("images")

        # Ensure image_sources is a list
        if not isinstance(image_sources, list):
            raise TypeError("Image value must be a list")

        # Initialize content
        content = []

        # Process each image
        for image_source in image_sources:
            image_content = format_image(image_source, vendor, detail)
            if image_content:
                content.append(image_content)

        # Handle text content
        content = handle_text_content(message, content)

        processed_message["content"] = content
        logger.debug("Processed message: %s", processed_message)
        return processed_message

    except TypeError as exc:
        raise TypeError(f"Error processing message: {exc}") from exc
    except (FileNotFoundError, OSError, Exception) as exc: # pylint: disable=broad-except
        raise Exception(f"Error processing message: {exc}") from exc  # pylint: disable=broad-exception-raised


def remove_images_from_message(message: dict) -> dict:
    """Remove images from a message."""
    if "images" in message:
        message = deepcopy(message)
        del message["images"]
    return message
