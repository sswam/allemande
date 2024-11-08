#!/usr/bin/env python3-allemande

# Version: 1.0.3

"""
This module processes rich text documents (DOCX, HTML, PDF) by applying a command to their text content.
"""

import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import re
from typing import List
from pathlib import Path
import subprocess

from argh import arg

from ally import main  # type: ignore

__version__ = "1.0.3"

logger = main.get_logger()


def process_docx(output_file: str, input_file: str, command: List[str]) -> None:
    """Process DOCX files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Unzip the DOCX file
        with zipfile.ZipFile(input_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Extract text from document.xml
        xml_file = Path(temp_dir) / 'word' / 'document.xml'
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Debug: Print all elements in the XML
        logger.debug("All elements in the XML:")
        for elem in root.iter():
            logger.debug(f"Element: {elem.tag}, Text: {elem.text}")

        # Process each text element separately
        matches = 0
        for elem in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'):
            if not elem.text:
                continue
            matches += 1
            logger.debug(f"Matching element found: {elem.tag}, Original text: {elem.text}")
            # Process the text using the command
            elem.text = subprocess.run(command, input=elem.text, text=True, stdout=subprocess.PIPE).stdout
            # result = subprocess.run(command, input=elem.text, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # elem.text = result.stdout
            # # If you need to do something with stderr:
            # # error_output = result.stderr
            logger.debug(f"Processed text: {elem.text}")

        logger.info(f"Total matching elements processed: {matches}")

        # Save the modified XML
        tree.write(xml_file, encoding='UTF-8', xml_declaration=True)

        # Zip the modified files back into a DOCX
        with zipfile.ZipFile(output_file, 'w') as zip_ref:
            for file in Path(temp_dir).rglob('*'):
                zip_ref.write(file, file.relative_to(temp_dir))

    logger.info(f"Processing complete. Output saved to {output_file}")


def process_html(output_file: str, input_file: str, command: List[str]) -> None:
    """Process HTML files."""
    # TODO: Implement HTML processing
    raise NotImplementedError("HTML processing not implemented yet.")


def process_pdf(output_file: str, input_file: str, command: List[str]) -> None:
    """Process PDF files."""
    # TODO: Implement PDF processing
    raise NotImplementedError("PDF processing not implemented yet.")


@arg('-f', '--force', help="Force overwrite of existing output file.")
def rich_text_process(output_file: str, input_file: str, command: List[str], force=False) -> None:
    """
    Process rich text documents by applying a command to their text content.

    Args:
        output_file (str): Path to the output file.
        input_file (str): Path to the input file.
        command (List[str]): Command to apply to the text content.
    """
    # Check if input file exists
    if not Path(input_file).is_file():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Check if output file already exists
    if not force and main.file_not_empty(output_file):
        raise FileExistsError(f"Output file already exists: {output_file}")

    # Determine file type and process accordingly
    file_extension = Path(input_file).suffix.lower()
    if file_extension == '.docx':
        process_docx(output_file, input_file, command)
    elif file_extension == '.html':
        process_html(output_file, input_file, command)
    elif file_extension == '.pdf':
        process_pdf(output_file, input_file, command)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

if __name__ == "__main__":
    main.run(rich_text_process)
