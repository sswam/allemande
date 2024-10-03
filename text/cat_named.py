#!/usr/bin/env python

"""
cat_named.py - A Python script to concatenate and display file contents with customizable headers.

This script can be used to read and display the contents of multiple files or URLs,
with options to add headers, numbering, and customize the output format.

Usage:
    python cat_named.py [OPTIONS] FILE1 [FILE2 ...] [URL1 [URL2 ...]]

This script can also be used as a module:
    from cat_named import cat_named
"""

import os
import sys
from pathlib import Path
import subprocess
from urllib.parse import urlparse
import re

from argh import arg

from ally import main

__version__ = "1.0.1"


logger = main.get_logger()


def get_web_content(url):
    """Fetch content from a URL using web_text tool."""
    try:
        result = subprocess.run(
            ["web_text", url], capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise FileNotFoundError(f"Failed to fetch content from {url}: {e}")


@arg("sources", nargs="*", help="Files or URLs to concatenate and display")
@arg("--header-pre", help="Prefix for the header line")
@arg("--header-post", help="Suffix for the header line")
@arg("--footer", help="String to append after each file's content")
@arg("--number", help="Number the files starting from this value")
@arg("--number-post", help="String to append after the number in the header")
@arg("--path", help="Search for files in PATH", action="store_true")
@arg(
    "--basename",
    help="Use only the basename of the file in the header",
    action="store_true",
)
@arg("-n", "--stdin-name", help="Use this name for stdin")
@arg("-f", "--missing-ok", help="Skip missing files without error", action="store_true")
def cat_named(
    sources,
    header_pre="#File: ",
    header_post="\n\n",
    footer="\n\n",
    number=None,
    number_post=". ",
    path=False,
    basename=False,
    stdin_name=None,
    missing_ok=False,
):
    """
    Concatenate and return file or URL contents with customizable headers.
    """
    if number is not None:
        number = int(number)

    result = []

    def get_header(source):
        nonlocal number
        if number is not None:
            header = f"{header_pre}{number}{number_post}{source}"
            number += 1
        else:
            header = f"{header_pre}{source}"
        return header

    for source in sources:
        is_url = source.startswith(("http://", "https://", "ftp://", "ftps://"))

        if is_url and basename:
            display_name = os.path.basename(urlparse(source).path)
        elif is_url:
            display_name = source
        elif basename:
            display_name = Path(source).name
        else:
            display_name = source

        try:
            if is_url:
                content = get_web_content(source)
            else:
                with main.TextInput(
                    source, search=path, basename=basename, stdin_name=stdin_name
                ) as istream:
                    content = istream.read()
                    display_name = istream.display

            header = get_header(display_name)

            result.append(f"{header}{header_post}")
            result.append(content)
            result.append(footer)
        except (FileNotFoundError, IsADirectoryError):
            if missing_ok:
                header = get_header(display_name)

                result.append(f"{header} (content missing){header_post}")
                result.append(footer)
            else:
                raise

    text = "".join(result)

    return text


if __name__ == "__main__":
    main.run(cat_named)
