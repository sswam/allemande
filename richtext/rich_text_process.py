#!/usr/bin/env python3

"""
This module processes rich text documents (DOCX, HTML, ODT) by applying a command to their text content.
"""

import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
import re
from typing import List
from pathlib import Path
import subprocess
import argparse
import logging
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed
from bs4 import BeautifulSoup

__version__ = "1.0.10"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def process_text(command, text):
    # we do not want to capture stderr
    return subprocess.run(command, input=text, text=True, stdout=subprocess.PIPE).stdout


def process_docx(output_file: str, input_file: str, command: List[str], punct: bool, pool=None) -> None:
    """Process DOCX files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Unzip the DOCX file
        with zipfile.ZipFile(input_file, 'r') as zip_ref:
            zip_ref.extractall(temp_path)

        # Extract text from document.xml
        xml_file = temp_path / 'word' / 'document.xml'
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Prepare the jobs
        jobs = [(elem, elem.text) for elem in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t')
                if elem.text and (punct or re.search(r'\w+', elem.text, re.UNICODE))]

        # Process in parallel or sequentially
        if pool:
            with ProcessPoolExecutor(max_workers=pool) as executor:
                future_to_elem = {executor.submit(process_text, command, text): (elem, text) for elem, text in jobs}
                for future in as_completed(future_to_elem):
                    elem, original_text = future_to_elem[future]
                    try:
                        elem.text = future.result()
                        logger.debug(f"Processed: Original: {original_text}, New: {elem.text}")
                    except Exception as exc:
                        logger.error(f'Generated an exception: {exc}')
        else:
            for elem, text in jobs:
                elem.text = process_text(command, text)
                logger.debug(f"Processed: Original: {text}, New: {elem.text}")

        logger.info(f"Total matching elements processed: {len(jobs)}")

        # Save the modified XML
        tree.write(xml_file, encoding='UTF-8', xml_declaration=True)

        # Zip the modified files back into a DOCX
        with zipfile.ZipFile(output_file, 'w') as zip_ref:
            for file in temp_path.rglob('*'):
                zip_ref.write(file, file.relative_to(temp_path))


def process_html(output_file: str, input_file: str, command: List[str], punct: bool, pool=None) -> None:
    """Process HTML files."""
    with open(input_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')

    text_nodes = soup.find_all(text=True)

    def process_text(text):
        if punct or re.search(r'\w+', text, re.UNICODE):
            if pool:
                return pool.apply(subprocess.run, (command, ), {'input': text, 'text': True, 'stdout': subprocess.PIPE}).stdout
            else:
                return subprocess.run(command, input=text, text=True, stdout=subprocess.PIPE).stdout
        return text

    for node in text_nodes:
        if node.parent.name not in ['script', 'style']:
            new_text = process_text(node.string)
            node.string = new_text

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(str(soup))

    logger.info(f"Processing complete. Output saved to {output_file}")


def process_odt(output_file: str, input_file: str, command: List[str], punct: bool, pool=None) -> None:
    """Process ODT files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Unzip the ODT file
        with zipfile.ZipFile(input_file, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Extract text from content.xml
        xml_file = Path(temp_dir) / 'content.xml'
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Process each text element separately
        matches = 0
        for elem in root.iter('{urn:oasis:names:tc:opendocument:xmlns:text:1.0}p'):
            if not elem.text:
                continue
            if punct or re.search(r'\w+', elem.text, re.UNICODE):
                matches += 1
                logger.debug(f"Matching element found: {elem.tag}, Original text: {elem.text}")
                # Process the text using the command
                if pool:
                    elem.text = pool.apply(subprocess.run, (command, ), {'input': elem.text, 'text': True, 'stdout': subprocess.PIPE}).stdout
                else:
                    elem.text = subprocess.run(command, input=elem.text, text=True, stdout=subprocess.PIPE).stdout
                logger.debug(f"Processed text: {elem.text}")

        logger.info(f"Total matching elements processed: {matches}")

        # Save the modified XML
        tree.write(xml_file, encoding='UTF-8', xml_declaration=True)

        # Zip the modified files back into an ODT
        with zipfile.ZipFile(output_file, 'w') as zip_ref:
            for file in Path(temp_dir).rglob('*'):
                zip_ref.write(file, file.relative_to(temp_dir))

    logger.info(f"Processing complete. Output saved to {output_file}")


def rich_text_process(output_file: str, input_file: str, command: List[str], force: bool = False, punct: bool = False, pool=None) -> None:
    """
    Process rich text documents by applying a command to their text content.

    Args:
        output_file (str): Path to the output file.
        input_file (str): Path to the input file.
        command (List[str]): Command to apply to the text content.
        force (bool): Force overwrite of existing output file.
        punct (bool): Process text without any words in it.
        pool: Multiprocessing pool for parallel processing.
    """
    # Check if input file exists
    if not Path(input_file).is_file():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Check if output file already exists
    if Path(output_file).exists():
        if not force:
            raise FileExistsError(f"Output file already exists: {output_file}")
        else:
            logger.warning(f"Overwriting existing output file: {output_file}")

    # Determine file type and process accordingly
    file_extension = Path(input_file).suffix.lower()
    if file_extension == '.docx':
        process_docx(output_file, input_file, command, punct, pool)
    elif file_extension == '.html':
        process_html(output_file, input_file, command, punct, pool)
    elif file_extension == '.odt':
        process_odt(output_file, input_file, command, punct, pool)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

def main():
    parser = argparse.ArgumentParser(description="Process rich text documents by applying a command to their text content.")
    parser.add_argument("output_file", help="Path to the output file")
    parser.add_argument("input_file", help="Path to the input file")
    parser.add_argument("command", nargs='+', help="Command to apply to the text content")
    parser.add_argument("-f", "--force", action="store_true", help="Force overwrite of existing output file")
    parser.add_argument("--punct", action="store_true", help="Process text without any words in it")
    parser.add_argument("-p", "--parallel", type=int, help="Number of parallel processes to use")
    args = parser.parse_args()

    try:
        if args.parallel:
            with multiprocessing.Pool(processes=args.parallel) as pool:
                rich_text_process(args.output_file, args.input_file, args.command, args.force, args.punct, pool=pool)
        else:
            rich_text_process(args.output_file, args.input_file, args.command, args.force, args.punct)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
