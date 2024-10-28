#!/usr/bin/env python3

"""
This module concatenates and displays file contents with customizable headers.

It can be used to read and display the contents of multiple files or URLs,
with options to add headers, numbering, and customize the output format.
"""

import os
import sys
import logging
from pathlib import Path
import subprocess
from urllib.parse import urlparse
import re
import argparse
from typing import List, Callable

from ally import main, old

__version__ = "1.0.2"

logger = main.get_logger()


def get_web_content(url: str) -> str:
    """Fetch content from a URL using web-text tool."""
    try:
        result = subprocess.run(["web-text", url], capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        raise FileNotFoundError(f"Failed to fetch content from {url}: {e}")


def number_the_lines(text: str) -> str:
    """Number the lines in the text, just number, tab, and line."""
    lines = text.splitlines()
    return "\n".join(f"{i+1}\t{line}" for i, line in enumerate(lines))


def cat_named(
    put: Callable[[str], None],
    *sources: str,
    number: int | None = None,
    number_suffix: str = ". ",
    path: bool = False,
    basename: bool = False,
    missing_ok: bool = False,
    number_lines: bool = False,
    header_prefix: str = "#File: ",
    header_suffix: str = "\n\n",
    footer: str = "\n\n",
    stdin_name: str | None = "input",
    suppress_headings: str | None = None,
) -> None:
    """
    Concatenate and return file or URL contents with customizable headers.
    """

    suppress_headings_list: list[str] = suppress_headings.split(",") if suppress_headings else []

    def get_header(source: str) -> str:
        nonlocal number
        if number is not None:
            header = f"{header_prefix}{number}{number_suffix}{source}"
            number += 1
        else:
            header = f"{header_prefix}{source}"
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
                with old.TextInput(
                    source,
                    search=path,
                    basename=basename,
                    stdin_name=stdin_name,
                    warn_deprecated=False,
                ) as istream:
                    content = istream.read()
                    display_name = istream.display


            if display_name not in suppress_headings_list:
                header = get_header(display_name)
                put(f"{header}{header_suffix}")

            if number_lines:
                content = number_the_lines(content)
            put(content)
            put(footer)
        except (FileNotFoundError, IsADirectoryError):
            if missing_ok:
                if display_name not in suppress_headings_list:
                    header = get_header(display_name)
                    put(f"{header} (content missing){header_suffix}")
                    put(footer)
            else:
                raise


def setup_args(parser: argparse.ArgumentParser) -> None:
    """Set up the command-line arguments."""
    add = parser.add_argument
    parser.description = "Concatenate and display file contents with customizable headers."
    add("sources", nargs="*", help="Files or URLs to concatenate and display")
    add("-n", "--number", type=int, help="Number files starting from this value")
    add("-p", "--path", action="store_true", help="Search for files in PATH")
    add("-b", "--basename", action="store_true", help="Use the file basename in the header")
    add("-f", "--missing-ok", action="store_true", help="Skip missing files without error")
    add("-N", "--number-lines", action="store_true", help="Number the lines in the output")
    add("-P", "--header-prefix", help="Prefix for the header line")
    add("-S", "--header-suffix", help="Suffix for the header line")
    add("-F", "--footer", help="String to append after each file's content")
    add("-H", "--suppress-headings", help="Comma-separated headings to suppress, e.g. input")
    add("--stdin-name", help="Use this name for stdin")
    add("--number-suffix", help="String to append after the number in the header")


if __name__ == "__main__":
    main.go(cat_named, setup_args)
