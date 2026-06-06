#!/usr/bin/env python3-allemande

"""
Tidy memory text by removing think blocks, START/STOP markers, and normalizing whitespace.
"""

import re
import pathlib
from typing import TextIO

from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


def tidy(text: str) -> str:
    """Remove think blocks, START/STOP markers, and normalize whitespace."""
    # Remove <think>...</think> blocks (can span lines)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # Remove any stray <think> or </think> tags
    text = re.sub(r"</?think>", "", text)
    # Remove **STOP** (with optional asterisks) from the very end
    text = re.sub(r"\**\bSTOP\**\s*\Z", "", text)
    # Remove from start through START** (can span lines)
    text = re.sub(r"\A.*?\bSTART\b\**", "", text, flags=re.DOTALL)
    # Strip each line and join
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)
    # Strip whole string
    return text.strip()


def memory_tidy(istream: TextIO, ostream: TextIO, files: list[str] | None = None) -> None:
    """Process files inplace, or stdin to stdout if no files are given."""
    if not files:
        ostream.write(tidy(istream.read()))
        return
    for path in files:
        logger.debug("processing %s", path)
        text = pathlib.Path(path).read_text()
        pathlib.Path(path).write_text(tidy(text))


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("files", nargs="*", help="files to process inplace")


if __name__ == "__main__":
    main.go(memory_tidy, setup_args)
