#!/usr/bin/env python3

"""
This module processes rich text documents (DOCX, HTML, ODT) by applying a command to their text content.
"""

import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import re
from pathlib import Path
import subprocess
import argparse
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed

from bs4 import BeautifulSoup

from ally import main

__version__ = "1.0.10"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_text(command: list[str], text: str) -> str:
    # we do not want to capture stderr
    return subprocess.run(command, input=text, text=True, stdout=subprocess.PIPE).stdout


def process_docx(
    output_file: str, input_file: str, command: list[str], punct: bool, executor=None
) -> None:
    """Process DOCX files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Unzip the DOCX file
        with zipfile.ZipFile(input_file, "r") as zip_ref:
            zip_ref.extractall(temp_path)

        # Extract text from document.xml
        xml_file = temp_path / "word" / "document.xml"
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Prepare the jobs
        jobs = [
            (elem, elem.text)
            for elem in root.iter("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t")
            if elem.text and (punct or re.search(r"\w+", elem.text, re.UNICODE))
        ]

        # Process in parallel
        future_to_elem = {
            executor.submit(process_text, command, text): (elem, text) for elem, text in jobs
        }
        for future in as_completed(future_to_elem):
            elem, original_text = future_to_elem[future]
            try:
                elem.text = future.result()
                logger.debug(f"Processed: Original: {original_text}, New: {elem.text}")
            except Exception as exc:
                logger.error(f"Generated an exception: {exc}")

        logger.info(f"Total matching elements processed: {len(jobs)}")

        # Save the modified XML
        tree.write(xml_file, encoding="UTF-8", xml_declaration=True)

        # Zip the modified files back into a DOCX
        with zipfile.ZipFile(output_file, "w") as zip_ref:
            for file in temp_path.rglob("*"):
                zip_ref.write(file, file.relative_to(temp_path))


def process_html(
    output_file: str, input_file: str, command: list[str], punct: bool, executor=None
) -> None:
    """Process HTML files."""
    with open(input_file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    text_nodes = soup.find_all(text=True)

    # Prepare the jobs
    jobs = [
        (node, node.string)
        for node in text_nodes
        if node.parent.name not in ["script", "style"] and (punct or re.search(r"\w+", node.string, re.UNICODE))
    ]

    # Process in parallel
    future_to_node = {
        executor.submit(process_text, command, text): (node, text) for node, text in jobs
    }
    for future in as_completed(future_to_node):
        node, original_text = future_to_node[future]
        try:
            node.string = future.result()
            logger.debug(f"Processed: Original: {original_text}, New: {node.string}")
        except Exception as exc:
            logger.error(f"Generated an exception: {exc}")

    logger.info(f"Total matching elements processed: {len(jobs)}")

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(str(soup))

    logger.info(f"Processing complete. Output saved to {output_file}")


def process_odt(
    output_file: str, input_file: str, command: list[str], punct: bool, executor=None
) -> None:
    """Process ODT files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Unzip the ODT file
        with zipfile.ZipFile(input_file, "r") as zip_ref:
            zip_ref.extractall(temp_dir)

        # Extract text from content.xml
        xml_file = Path(temp_dir) / "content.xml"
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Prepare the jobs
        jobs = [
            (elem, elem.text)
            for elem in root.iter("{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p")
            if elem.text and (punct or re.search(r"\w+", elem.text, re.UNICODE))
        ]

        # Process in parallel
        future_to_elem = {
            executor.submit(process_text, command, text): (elem, text) for elem, text in jobs
        }
        for future in as_completed(future_to_elem):
            elem, original_text = future_to_elem[future]
            try:
                elem.text = future.result()
                logger.debug(f"Processed: Original: {original_text}, New: {elem.text}")
            except Exception as exc:
                logger.error(f"Generated an exception: {exc}")

        logger.info(f"Total matching elements processed: {len(jobs)}")

        # Save the modified XML
        tree.write(xml_file, encoding="UTF-8", xml_declaration=True)

        # Zip the modified files back into an ODT
        with zipfile.ZipFile(output_file, "w") as zip_ref:
            for file in Path(temp_dir).rglob("*"):
                zip_ref.write(file, file.relative_to(temp_dir))

    logger.info(f"Processing complete. Output saved to {output_file}")


def rich_text_process(
    output_file: str,
    input_file: str,
    *command: str,
    force: bool = False,
    punct: bool = False,
    parallel: int | None = 1,
) -> None:
    """Process rich text documents by applying a command to their text content."""

    # Check if input file exists
    if not Path(input_file).is_file():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Check if output file already exists
    if Path(output_file).exists():
        if not force:
            raise FileExistsError(f"Output file already exists: {output_file}")
        else:
            logger.warning(f"Overwriting existing output file: {output_file}")

    with ProcessPoolExecutor(max_workers=parallel) as executor:
        # Determine file type and process accordingly
        file_extension = Path(input_file).suffix.lower()
        if file_extension == ".docx":
            process_docx(output_file, input_file, command, punct, executor)
        elif file_extension == ".html":
            process_html(output_file, input_file, command, punct, executor)
        elif file_extension == ".odt":
            process_odt(output_file, input_file, command, punct, executor)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")


def setup_args(arg) -> None:
    """Set up the command-line arguments."""
    arg("output_file", help="Path to the output file")
    arg("input_file", help="Path to the input file")
    arg("command", nargs="+", help="Command to apply to the text content")
    arg("-f", "--force", action="store_true", help="Force overwrite of existing output file")
    arg("--punct", action="store_true", help="Process text without any words in it")
    arg("-p", "--parallel", type=int, help="Number of parallel processes to use")


if __name__ == "__main__":
    main.go(rich_text_process, setup_args)
