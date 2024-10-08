#!/usr/bin/env python3

"""
This module generates code to support long and short options based on the script's content.
"""

import os
import sys
import re
from typing import TextIO
import mimetypes

from argh import arg

from ally import main

__version__ = "0.1.0"

logger = main.get_logger()


def process_line(line: str) -> str:
    """Process a single line of the script."""
    # Remove indent and 'local ' from start of line
    line = line.lstrip()
    line = re.sub(r'^local\s+', '', line)

    # Extract variable name, short option, and default value
    match = re.match(r'(\w+)=(\S*)\s+(\w+)=(\S*)\s+#\s*(.*)', line)
    if match:
        long_opt, _default_1, short_opt, _default_2, description = match.groups()
        if _default_2.startswith("("):
            return f'{long_opt}=(${{{long_opt}[@]}} ${{{short_opt}[@]}}); unset {short_opt}'
        else:
            return f'{long_opt}=${{{long_opt}:-${short_opt}}}; unset {short_opt}'

    return None


@arg("script", help="Path to the script file to process")
def opts_long(
    script: str,
    istream: TextIO = sys.stdin,
    ostream: TextIO = sys.stdout,
) -> None:
    """
    Generate code to support long and short options based on the script's content.
    """
    get, put = main.io(istream, ostream)

    try:
        with open(script, "r") as istream:
            for line in istream:
                line = line.strip()

                # Stop before the ". opts" line
                if re.match(r'\s*\.\s+opts', line):
                    break

                # Stop before an eval line
                if re.match(r'\s*eval\s', line):
                    break

                # Process and output the line
                processed_line = process_line(line)
                if processed_line:
                    put(processed_line + "\n")
    except (FileNotFoundError, IsADirectoryError, UnicodeDecodeError) as e:
        logger.info(f"File not found: {script}")


if __name__ == "__main__":
    main.run(opts_long)
