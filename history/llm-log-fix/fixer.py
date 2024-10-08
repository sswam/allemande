#!/usr/bin/env python3

"""
This module fixes filename issues by creating prompt files from answer files.
"""

import os
import sys
import logging
from typing import TextIO

from argh import arg

from ally import main

__version__ = "0.1.1"

logger = main.get_logger()


def create_prompt_file(answer_file: str) -> None:
    """Create a prompt file based on the answer file name, copy its mtime and atime."""
    prompt_file = answer_file.replace(".answer.", ".prompt.")
    if main.file_not_empty(prompt_file):
        logger.info(f"Prompt file already exists: {prompt_file}")
        return

    timestamp, content = answer_file.split(".answer.")
    content = content.replace("_", " ")
    with open(prompt_file, "w") as f:
        f.write(content)

    # Copy mtime and atime from answer file to prompt file
    answer_stats = os.stat(answer_file)
    os.utime(prompt_file, (answer_stats.st_atime, answer_stats.st_mtime))

    logger.info(f"Created prompt file: {prompt_file}")


def fixer(
    *filenames: list[str],
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Process a list of answer filenames and create corresponding prompt files.
    """
    get, put = main.io(istream, ostream)

    if not filenames:
        logger.info("No filenames provided. Nothing to do.")
        return

    for filename in filenames:
        if not ".answer." in filename:
            logger.warning(f"Skipping non-answer file: {filename}")
            continue

        create_prompt_file(filename)


if __name__ == "__main__":
    main.run(fixer)
