#!/usr/bin/env python3

"""
This module reformats source code using external tools.
"""

import subprocess
import logging
from typing import TextIO

import black

from ally import main, resource, lazy, geput

__version__ = "0.1.1"

logger = main.get_logger()


def run(cmd: list[str], input_str: str) -> str:
    """Run a command with input and return its output."""
    return subprocess.run(cmd, input=input_str.encode(), capture_output=True).stdout.decode()


def reformat(
    *filenames: list[str],
    istream: TextIO,
    put: geput.Put,
    language: str = "py",
    fatal: bool = False,
) -> None:
    """Reformat the source code using external tools"""
    source = get(all=True)

    try:
        if language == "py":
            source = black.format_str(source, mode=black.FileMode())
        elif language == "sh":
            source = run(["shfmt"], source)
        elif language == "pl":
            source = run(["perltidy"], source)
        elif language == "c":
            style_file = resource("c/clang-format-style")
            source = run(["clang-format", f"-style=file:{style_file}"], source)
        else:
            logger.warning(f"Unsupported language: {language}")
    except (black.InvalidInput, subprocess.CalledProcessError) as e:
        logger.error(f"Reformatting failed: {e}")
        if fatal:
            raise
        # if not fatal, use the original source code

    put(source)


def setup_args(arg):
    arg("--language", help="Source code language (default: py)")


if __name__ == "__main__":
    main.go(reformat, setup_args)
