#!/usr/bin/env python3-allemande

"""
This module enhances text in an image by cleaning up the input,
using OCR, correcting transcription errors with an LLM,
erasing and inpainting the original text,
and replacing the text in the image.

This version uses Pango/Cairo for text rendering.
Note: The normal way to do alpha channels feels wrong to me,
so I am using 0 for opaque and 255 for transparent.
"""

import sys
import logging
from typing import TextIO, Callable, Any
import re
import math

import cv2
import numpy as np
from scipy import stats  # type: ignore
import pytesseract  # type: ignore
import cairo
import gi  # type: ignore
gi.require_version('Pango', '1.0')
gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo  # type: ignore

from ally import main, logs, lazy, geput  # type: ignore
import llm  # type: ignore

__version__ = "0.1.8"

logger = logs.get_logger()


def enhance_image(image: np.ndarray) -> np.ndarray:
    """Apply image enhancement techniques."""
    # Sharpen the image
    kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
    sharpened = cv2.filter2D(image, -1, kernel)

    # Increase contrast
    lab = cv2.cvtColor(sharpened, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    enhanced = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

    return enhanced


def ocr_image(image: np.ndarray) -> list[list[dict[str, Any]]]:
    """Perform OCR on the image and return words with bounding boxes and line information."""
    data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    lines = []
    current_line = []

    n_boxes = len(data["level"])
    for i in range(n_boxes):
        level = data["level"][i]
        text = data["text"][i].strip()

        if level == 5 and text:  # Word-level data
            word_box = {
                "text": text,
                "left": data["left"][i],
                "top": data["top"][i],
                "width": data["width"][i],
                "height": data["height"][i],
            }
            current_line.append(word_box)
        elif level == 4 and current_line:  # End of line
            lines.append(current_line)
            current_line = []

    if current_line:  # Handle last line if exists
        lines.append(current_line)

    return lines


def prepare_ocr_results(words: list[list[dict[str, Any]]]) -> str:
    """Prepare OCR results for LLM processing."""
    result = ""
    for line_num, line in enumerate(words, 1):
        result += f"## Line {line_num}:\n\n"
        for word_num, word in enumerate(line, 1):
            result += f"{word_num}. {word['text']}\n"
        result += "\n"
    return result.strip()


def correct_text(model: str, ocr_results: str, vocab: str | None = None) -> str:
    """Correct OCR errors using an LLM."""
    custom_vocab_prompt = f"Custom vocabulary context: {vocab}\n" if vocab else ""

    prompt = f"""
Please correct the OCR errors in this list of words.
Remove any spurious characters and ensure correct formatting.
Only return the corrected words, maintaining the original structure and numbering.
Some words may map to nothing (empty string), and some may map to multiple words if incorrectly concatenated.
{custom_vocab_prompt}

--- START LIST ---
{ocr_results}
--- END LIST ---
"""
    return llm.query(prompt, model=model)


def set_list_at(the_list, index, value, item_name, default=None):
    """Set a value at a specific index in a list, filling in any gaps with a default value."""
    if index != len(the_list):
        logger.warning(f"Unexpected {item_name} number: {index+1}, expected: {len(the_list)+1}")
    if index < len(the_list):
        raise ValueError(f"{item_name.title()} numbers must be strictly increasing")
    the_list.extend([default] * (index - len(the_list) + 1))
    the_list[index] = value


def parse_corrected_text(corrected: str) -> list[list[tuple[int, str]]]:
    """Parse the corrected text from the LLM back into a structured format."""
    lines: list[list[tuple[int, str]]] = []
    current_line: list[tuple[int, str]] = []
    line_pattern = r"^#*\s*Line (\d+):?$"
    word_pattern = r"^\s*(\d+)\.\s*(.*)$"

    for line in corrected.strip().splitlines():
        if line_match := re.match(line_pattern, line):
            if current_line:
                current_line = []
            line_num = int(line_match.group(1)) - 1  # 0-based index
            set_list_at(lines, line_num, current_line, "line", [])
        elif word_match := re.match(word_pattern, line):
            index, word = word_match.groups()
            index = int(index) - 1  # 0-based index
            set_list_at(current_line, index, (index, word), "word", (-1, ""))

    if current_line:
        lines.append(current_line)

    return lines


def filter_lines(lines: list[list[dict[str, Any]]], corrected_lines: list[list[tuple[int, str]]]) -> list[str]:
    """Filter out mistaken 'words' from the OCR results."""
    filtered_lines = []
    for ocr_line, corrected_line in zip(lines, corrected_lines):
        filtered_line = []
        for ocr_word, (_index, corrected_word) in zip(ocr_line, corrected_line):
            if corrected_word:
                filtered_line.append(corrected_word)

        if not filtered_line:
            continue

        filtered_lines.append(" ".join(filtered_line))
    return filtered_lines


def get_line_boxes(lines: list[list[dict[str, Any]]], corrected_lines: list[list[tuple[int, str]]]) -> list[dict[str, int]]:
    """Get bounding boxes for each corrected line."""
    boxes = []
    for ocr_line, corrected_line in zip(lines, corrected_lines):
        filtered_words = [word for word, corrected_word in zip(ocr_line, corrected_line) if corrected_word[1]]

        if not filtered_words:
            continue

        left = min(word["left"] for word in filtered_words)
        top = min(word["top"] for word in filtered_words)
        right = max(word["left"] + word["width"] for word in filtered_words)
        bottom = max(word["top"] + word["height"] for word in filtered_words)

        boxes.append({
            "left": left,
            "top": top,
            "width": right - left,
            "height": bottom - top,
        })

    return boxes


def get_font_size(text: str, max_width: int, max_height: int, font_path: str, max_compression: float = 0.85) -> int:
    """Calculate the maximum font size that fits within the given dimensions."""
    logger.debug(f"Calculating font size for text: {text}, width={max_width}, height={max_height}")

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, max_width, max_height)
    context = cairo.Context(surface)

    layout = PangoCairo.create_layout(context)
    font_size = max_height * 2  # should be less, but whatever for the moment

    while font_size > 1:
        font = Pango.FontDescription(f"{font_path} {font_size}")
        layout.set_font_description(font)
        layout.set_text(text)

        width, height = layout.get_pixel_extents()[0].width, layout.get_pixel_extents()[0].height

        if width <= max_width / max_compression and height <= max_height:
            break

        font_size -= 1

    return font_size


def render_text_in_box(text: str, width: int, height: int, font_size: int, font_path: str) -> np.ndarray:
    """Render text using Pango/Cairo."""
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    context = cairo.Context(surface)

    # paint white background
    context.set_source_rgb(1, 1, 1)
    context.paint()

    layout = PangoCairo.create_layout(context)
    font = Pango.FontDescription(f"{font_path} {font_size}")
    layout.set_font_description(font)
    layout.set_width(-1)  # No wrapping

    # Justify the text, probably obliviates the need for letter spacing
    layout.set_justify(True)
    layout.set_justify_last_line(True)

    layout.set_text(text)

    attrs = Pango.AttrList()

    attrs.insert(Pango.attr_foreground_new(0, 0, 0))

    # Adjust letter spacing to fit width if necessary
    ink_rect, logical_rect = layout.get_pixel_extents()
    text_width = ink_rect.width
    if text_width != width and len(text) > 1:
        letter_spacing = math.floor((width - text_width) / (len(text) - 1) * Pango.SCALE)
        logger.debug(f"{text_width=} {width=} {letter_spacing=}")
        attrs.insert(Pango.attr_letter_spacing_new(letter_spacing))

    layout.set_attributes(attrs)

    context.translate(-ink_rect.x, -ink_rect.y)
    PangoCairo.show_layout(context, layout)

    buf = surface.get_data()
    img_array: np.ndarray = np.ndarray(shape=(height, width, 4), dtype=np.uint8, buffer=buf)
    invert_alpha_channel(img_array)
    return img_array


def solve_quadratic(a, b, c):
    """Solve a quadratic equation of the form ax^2 + bx + c = 0."""
    # Calculate the discriminant
    d = b**2 - 4*a*c

    if d < 0:
        return None, None

    # Find two solutions
    root_d = math.sqrt(d)
    sol1 = (-b - root_d) / (2*a)
    sol2 = (-b + root_d) / (2*a)

    return sol1, sol2


def make_dark_and_light_areas_transparent(image, box, std_dev_factor=0.25, grow=0.1):
    """Make dark and light areas of the image transparent within the box, i.e. the previous text."""
    # TODO handle foreground and background colors of similar brightness

    # Grow the box slightly to include surrounding areas, for better stats
    # Need to solve (width + d) * (height + d) = (width * height * (1 + grow))
    # It's a quadratic equation, solve for d

    # The coefficients of the quadratic equation
    a = 1
    b = box["width"] + box["height"]
    c = -box["width"] * box["height"] * ((grow + 1)**2 - 1)

    sol1, sol2 = solve_quadratic(a, b, c)
    assert sol1 is not None and sol2 is not None, "No valid solution found for box growth"

    d = round(max(sol1, sol2))
    assert d > 0, "Invalid box growth value"

    # Expand the box
    context_box = {
            "left": max(0, box["left"] - d),
            "top": max(0, box["top"] - d),
            "right": min(image.shape[1], box["left"] + box["width"] + d),
            "bottom": min(image.shape[0], box["top"] + box["height"] + d),
    }
    context_box["width"] = context_box["right"] - context_box["left"]
    context_box["height"] = context_box["bottom"] - context_box["top"]

    # Extract the context region
    context = image[context_box["top"]:context_box["bottom"], context_box["left"]:context_box["right"]]

    # Convert context to grayscale
    gray_context = np.mean(context[:,:,:3], axis=2).astype(np.uint8)

    # Calculate mode and standard deviation
    mode = stats.mode(gray_context, axis=None)[0]
    std_dev = np.std(gray_context)

    # Calculate light and dark thresholds
    light_threshold = min(255, mode + std_dev_factor * std_dev)
    dark_threshold = max(0, mode - std_dev_factor * std_dev)

    # Extract the region of interest (ROI)
    roi = image[box["top"]:box["top"]+box["height"], box["left"]:box["left"]+box["width"]]

    # Convert ROI to grayscale
    gray_roi = np.mean(roi[:,:,:3], axis=2).astype(np.uint8)

    # Create a mask for pixels to remove (too light or too dark)
    mask = (gray_roi < dark_threshold) | (gray_roi > light_threshold)

    # Apply the mask to the alpha channel of the ROI
    roi[:,:,3] = mask * 255

    # Update the image with the modified ROI
    image[box["top"]:box["top"]+box["height"], box["left"]:box["left"]+box["width"]] = roi

    return image


def overlay_images(background, foreground):
    """Overlay an RGBA image over another RGBA image, giving an RGBA result."""
    alpha = foreground[:,:,3] / 255.0
    bg_alpha = background[:,:,3] / 255.0
    alpha_3d = np.stack([alpha]*3, axis=2)
    result = background[:,:,:3] * alpha_3d + foreground[:,:,:3] * (1 - alpha_3d)
    result_alpha = alpha * bg_alpha * 255
    return np.dstack((result, result_alpha)).astype(np.uint8)


def image_apply_background(image: np.ndarray, background_rgba: tuple[int, int, int, int] = (255, 255, 255, 0)) -> np.ndarray:
    """If the image has an alpha channel, apply it over a background color."""
    if image.shape[2] == 4:
        background = np.full(image.shape, background_rgba, dtype=np.uint8)
        image = overlay_images(background, image)
    else:
        image = image.copy()
    return image


def show_image(image: np.ndarray, background_rgba=(255, 196, 0, 0), title="Rendered Text"):
    """Show the image in a window."""
    image = image_apply_background(image, background_rgba)[:,:,:3]
    # invert_alpha_channel(image)

    # Show the rendered_text in a window
    cv2.imshow(title, image)
    cv2.waitKey(0)
    cv2.destroyWindow(title)


def invert_alpha_channel(image: np.ndarray):
    """Invert the alpha channel of an image, for my convention where 0 is opaque and 255 is transparent."""
    image[:, :, 3] = 255 - image[:, :, 3]


def replace_text_in_image(
    image: np.ndarray, boxes: list[dict[str, Any]], lines: list[str], font_path: str
) -> np.ndarray:
    """Replace the original text in the image with corrected text using Pango/Cairo."""
    result_image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

    invert_alpha_channel(result_image)

    # Erase the original text to transparent
    for box, line in zip(boxes, lines):
        if not line:
            continue

        result_image = make_dark_and_light_areas_transparent(result_image, box)

    # Inpaint the erased parts of the background
    result_image = inpaint(result_image)

    # Overlay the corrected text on the image
    for box, line in zip(boxes, lines):
        if not line:
            continue

        logger.debug(f"Replacing text in image: {line}")

        # Render the text using Pango/Cairo
        font_size = get_font_size(line, box["width"], box["height"], font_path)
        rendered_text = render_text_in_box(line, box["width"], box["height"], font_size, font_path)

        # show_image(rendered_text, title=f"Rendered Text for {line}")

        # Set alpha channel based on blue channel and make the image black
        rendered_text[:, :, 3] = rendered_text[:, :, 0]  # Set alpha channel based on blue channel
        rendered_text[:, :, :3] = 0   # Set RGB channels to black

        # show_image(rendered_text, title=f"Transparent Text for {line}")

        # Get the coordinates of the box
        x, y = int(box["left"]), int(box["top"])
        w, h = int(box["width"]), int(box["height"])

        # Ensure the rendered text matches the box size
        # This probably is not necessary, could be useful if we want to stretch the text
        logger.debug(f"Resizing text to fit box, from {rendered_text.shape[:2]} to {(h, w)}")
        rendered_text = cv2.resize(rendered_text, (w, h), interpolation=cv2.INTER_LANCZOS4)

        # show_image(rendered_text, title=f"Resized Text for {line}")

        # Overlay the rendered text on the specific area of the image
        result_image[y:y+h, x:x+w] = overlay_images(result_image[y:y+h, x:x+w], rendered_text)

        # show_image(result_image, title=f"Image with Text for {line}")

    return result_image


def inpaint(image: np.ndarray) -> np.ndarray:
    """Inpaint the erased parts of the background."""
    mask = image[:, :, 3] == 255
    image = image[:, :, :3]
    inpainted_image = cv2.inpaint(image, mask.astype(np.uint8), inpaintRadius=3, flags=cv2.INPAINT_TELEA)
    alpha = np.full(image.shape[:2], 0, dtype=np.uint8)
    inpainted_image = np.dstack((inpainted_image, alpha))
    return inpainted_image


def image_fix_text(
    input_path: str,
    output_path: str,
    model: str = "default",
    font: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    vocab: str | None = None,
) -> None:
    """
    Enhance text in an image by cleaning up the input,
    using OCR, correcting transcription errors, and
    replacing the original text in the image.
    """
    # Read and enhance the image
    image = cv2.imread(input_path)
    enhanced_image = enhance_image(image)

    # Perform OCR
    ocr_lines = ocr_image(enhanced_image)
    ocr_lines_str = "\n".join(" ".join(word["text"] for word in line) for line in ocr_lines)
    logger.info(f"OCR Result:\n{ocr_lines_str}\n")

    # Correct text using LLM
    ocr_results = prepare_ocr_results(ocr_lines)
    response = correct_text(model, ocr_results, vocab)
    corrected_lines = parse_corrected_text(response)
    logger.debug(f"Corrected Lines: {corrected_lines}")
    corrected_lines_str = "\n".join(" ".join(word[1] for word in line) for line in corrected_lines)
    logger.info(f"Corrected Text:\n{corrected_lines_str}\n")

    # Filter out mistaken 'words', and set line bounding boxes
    filtered_lines = filter_lines(ocr_lines, corrected_lines)
    boxes = get_line_boxes(ocr_lines, corrected_lines)
    logger.info(f"Filtered Lines:\n{'\n'.join(filtered_lines)}\n")

    # Replace text in the image
    result_image = replace_text_in_image(image, boxes, filtered_lines, font)
    invert_alpha_channel(result_image)

    # Save the result
    cv2.imwrite(output_path, result_image)
    logger.info(f"Enhanced image saved to: {output_path}")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("input_path", help="path to the input image")
    arg("output_path", help="path to save the output image")
    arg("--model", "-m", help="LLM model to use")
    arg("--font", "-f", help="path to the font file")
    arg("--vocab", "-V", help="custom vocabulary for context in text correction")


if __name__ == "__main__":
    main.go(image_fix_text, setup_args)


# TODO could choose fonts from candidates based on metrics
