#!/usr/bin/env python3-allemande

"""
Convert Whisper STT JSON output to TSV with timestamps.

Reads JSON chunks with timestamps and text, outputs TSV format where:
- First column is the start timestamp
- Second column is the text
- Multi-line text has continuation lines indented with a tab
"""

import json
import sys
from typing import TextIO

from ally import main  # type: ignore

__version__ = "0.1.0"


def format_chunk(timestamp: float, text: str) -> str:
    """Format a chunk with timestamp and text, handling multi-line text."""
    lines = text.split('\n')

    if len(lines) == 1:
        return f"{timestamp}\t{text}\n"

    # Multi-line: first line with timestamp, rest indented
    result = f"{timestamp}\t{lines[0]}\n"
    for line in lines[1:]:
        result += f"\t{line}\n"

    return result


def transcript_to_history(
    istream: TextIO,
    ostream: TextIO,
) -> None:
    """Convert Whisper STT JSON output to TSV with timestamps."""
    data = json.load(istream)
    chunks = data.get("chunks", [])

    for chunk in chunks:
        timestamp_array = chunk.get("timestamp", [])
        if not timestamp_array:
            continue

        start_time = timestamp_array[0]
        text = chunk.get("text", "")

        output = format_chunk(start_time, text)
        ostream.write(output)


def setup_args(arg):
    """Set up the command-line arguments."""


if __name__ == "__main__":
    main.go(transcript_to_history, setup_args)
