#!/usr/bin/env python3

"""
This module applies style guidelines to specified files based on their extensions.
"""

import sys
import os
from pathlib import Path
import argparse
import logging
from typing import List

from ally import main

__version__ = "0.1.1"

logger = main.get_logger()

def apply_style(files: List[str]) -> None:
    """Apply style guidelines to the specified files."""
    if not files:
        raise ValueError("No files provided.")

    extension_to_language = {
        'sh': 'bash',
        'py': 'python'
    }

    extensions = set()

    for file in files:
        file_path = Path(file)
        ext = file_path.suffix.lstrip('.') or "sh"

        if ext not in extension_to_language:
            raise ValueError(f"Unsupported program file extension: {file}")

        extensions.add(ext)

    home = Path(os.environ["ALLEMANDE_HOME"])

    for ext in extensions:
        lang = extension_to_language[ext]
        hello_script = home / lang / f"hello_{ext}.{ext}"
        logger.info(f"Style script: {hello_script}")

def setup_args(parser: argparse.ArgumentParser) -> None:
    """Set up the command-line arguments."""
    parser.description = "Apply style guidelines to specified files."
    parser.add_argument("files", nargs="+", help="Files to process")

if __name__ == "__main__":
    main.go(setup_args, apply_style)
