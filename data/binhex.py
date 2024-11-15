#!/usr/bin/env python3-allemande

"""
Encode and decode binary data in hexadecimal format.
"""

import sys
import logging
import binascii
from ally import main, logs  # type: ignore

__version__ = "0.1.0"

logger = logs.get_logger()


def encode(input_stream: bytes) -> bytes:
    """Encode binary data to hexadecimal."""
    return binascii.b2a_hex(input_stream)


def decode(input_stream: bytes) -> bytes:
    """Decode hexadecimal data to binary."""
    return binascii.a2b_hex(input_stream)


def binhex(decode_mode: bool = False) -> None:
    """Convert binary data to/from hexadecimal format."""
    try:
        input_data = sys.stdin.buffer.read()
        if decode_mode:
            logger.debug("Decoding hex to binary")
            output = decode(input_data)
        else:
            logger.debug("Encoding binary to hex")
            output = encode(input_data)

        sys.stdout.buffer.write(output)
        sys.stdout.buffer.flush()

    except binascii.Error as e:
        raise RuntimeError(f"Invalid hexadecimal data: {e}")


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-d", "--decode", dest="decode_mode", action="store_true",
        help="decode hex to binary (default is encode)")


if __name__ == "__main__":
    main.go(binhex, setup_args)
