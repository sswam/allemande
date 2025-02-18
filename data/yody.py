#!/usr/bin/env python3-allemande

"""
Read and write files with YAML headers and text body, separated by double newline.
"""

from typing import TextIO, Any
import argparse
import logging
import sys

import yaml

from ally import main, logs  # type: ignore

__version__ = "0.1.1"

logger = logs.get_logger()


def read_yody(istream: TextIO) -> tuple[dict[str, Any], str]:
    """Read a YAML header and text body from a stream.

    Returns a tuple of (header_dict, body_text).
    """
    content = istream.read()

    if "\n\n" not in content:
        raise ValueError("No header separator (double newline) found")

    header_text, body = content.split("\n\n", 1)

    try:
        header = yaml.safe_load(header_text)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML header: {e}") from e

    if not isinstance(header, dict):
        raise ValueError("Header must be a YAML dictionary")

    return header, body.lstrip()  # Remove leading newline from body


def write_yody(header: dict[str, Any], body: str, ostream: TextIO) -> None:
    """Write a YAML header and text body to a stream."""
    header_text = yaml.dump(header, default_flow_style=False)
    ostream.write(header_text.rstrip())  # Remove trailing newlines from YAML dump
    ostream.write("\n\n")
    ostream.write(body)


def yody(infile: TextIO = sys.stdin, outfile: TextIO = sys.stdout) -> None:
    """Process YAML-header and text-body files."""
    logger.info("Reading input")
    header, body = read_yody(infile)

    logger.debug("Header: %s", header)
    logger.debug("Body length: %d", len(body))

    logger.info("Writing output")
    write_yody(header, body, outfile)


def setup_args(arg):
    """Set up command-line arguments."""
    arg("-i", "--infile", type=argparse.FileType("r"), default=sys.stdin, help="input file (default: stdin)")
    arg("-o", "--outfile", type=argparse.FileType("w"), default=sys.stdout, help="output file (default: stdout)")


if __name__ == "__main__":
    main.go(yody, setup_args)
