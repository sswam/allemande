#!/usr/bin/env python3-allemande

"""
Convert text into URL-friendly slugs.
"""

import re
import sys
from typing import TextIO
import argparse

from ally import main, geput, logs
from ally.geput import Get, Put
from argh import arg

__version__ = "0.1.1"

logger = logs.get_logger()


def slug(
    text: str = None,
    get: Get = None,
    put: Put = None,
    underscore: bool = False,
    boolean: bool = True,
    lower: bool = False,
    upper: bool = False,
) -> list[str] | None:
    """Convert text into URL-friendly slugs."""

    def process_text(input_text: str) -> str:
        if boolean:
            input_text = re.sub(r"&", "_and_", input_text)
            input_text = re.sub(r"\|", "_or_", input_text)

        input_text = re.sub(r"[^a-zA-Z0-9]", "_", input_text)
        input_text = re.sub(r"_+", "_", input_text)
        input_text = re.sub(r"^_|_$", "", input_text)

        if not input_text:
            input_text = "_"

        if lower:
            input_text = input_text.lower()
        elif upper:
            input_text = input_text.upper()

        if not underscore:
            input_text = re.sub(r"_", "-", input_text)

        return input_text

    print = geput.print(put)

    if text is not None:
        result = process_text(text)
        return result
    else:
        while (line := get()) is not None:
            slug = process_text(line)
            print(slug)
        return


def setup_args(arg) -> None:
    """Set up the command-line arguments."""
    arg("text", help="text to be slugified")
    arg("-u", "--underscore", help="use underscores", action="store_true")
    arg("-B", "--no-boolean", help="do not replace & and |", dest="boolean", action="store_false")
    arg("-l", "--lower", help="convert to lowercase", action="store_true")
    arg("-U", "--upper", help="convert to uppercase", action="store_true")


if __name__ == "__main__":
    main.go(slug, setup_args)


"""
FIXME: Improve handling of non-ASCII characters
TODO: Consider adding option to preserve case of input text
"""
