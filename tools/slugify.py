#!/usr/bin/env python3

"""
slugify.py: Convert text into URL-friendly slugs.
"""

import re
import sys
from typing import Union, List, TextIO

from ally import main
from argh import arg

__version__ = "0.1.1"

logger = main.get_logger()


def process_stream(stream: TextIO):
    """Process input stream line by line."""
    for line in stream:
        yield line.rstrip("\n")


@arg("-u", "--underscore", help="use underscores", dest="hyphen", action="store_false")
@arg(
    "-B",
    "--no-boolean",
    help="do not replace & and |",
    dest="boolean",
    action="store_false",
)
@arg("-l", "--lower", help="convert to lowercase", action="store_true")
@arg("-U", "--upper", help="convert to uppercase", action="store_true")
def slugify(
    *text: str,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
    hyphen: bool = True,
    boolean: bool = True,
    lower: bool = False,
    upper: bool = False,
) -> Union[str, List[str]]:
    """Convert text into URL-friendly slugs."""
    get, put = main.io(istream, ostream)

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

        if hyphen:
            input_text = re.sub(r"_", "-", input_text)

        return input_text

    if text:
        result = process_text(" ".join(text))
        return result
    else:
        while (line := get()) is not None:
            slug = process_text(line)
            put(slug)
        return


if __name__ == "__main__":
    main.run(slugify)

"""
TODO: Add support for custom replacement characters
FIXME: Improve handling of non-ASCII characters
XXX: Consider adding option to preserve case of input text
"""
