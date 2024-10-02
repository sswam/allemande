#!/usr/bin/env python3

"""
This module reformats source code using external tools.
"""

import subprocess
import logging
from typing import List

import black
from argh import arg

from ally import main, resource
from ally.lazy import lazy

__version__ = "0.1.1"

logger = main.get_logger()


def run(cmd: List[str], input_str: str) -> str:
    """Run a command with input and return its output."""
    return subprocess.run(cmd, input=input_str.encode(), capture_output=True).stdout.decode()


@arg("--language", help="Source code language (default: py)")
def reformat(
    *filenames: List[str],
    istream=None,
    ostream=None,
    language: str = "py",
    fatal: bool = False,
) -> None:
    """Reformat the source code using external tools"""
    get, put = main.io(istream, ostream)
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


if __name__ == "__main__":
    main.run(reformat)
