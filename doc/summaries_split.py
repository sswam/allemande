#!/usr/bin/env python3-allemande

"""
Split a file of character summaries into individual files by character name.
Each summary line starts with '- ' and contains a name between that and ' - '.
"""

import sys
from pathlib import Path

from ally import main, logs  # type: ignore

__version__ = "0.1.1"

logger = logs.get_logger()


def process_line(line: str, output_dir: Path) -> None:
    """Process a single line and write to appropriate file if it's a summary."""
    if not line.startswith("- "):
        return

    # Extract name between '- ' and ' - '
    parts = line.split(" - ", 1)
    if len(parts) < 2:
        return

    name = parts[0].lstrip("- ")
    output_file = output_dir / f"{name}.txt"

    logger.debug("Writing summary for %s to %s", name, output_file)
    output_file.write_text(parts[1] + "\n")


def split_summaries(output_dir: str = "summary") -> None:
    """Split character summaries into individual files."""
    out_path = Path(output_dir)
    out_path.mkdir(exist_ok=True)

    for line in sys.stdin:
        process_line(line.strip(), out_path)


def setup_args(arg):
    """Set up the command-line arguments."""
    arg("-o", "--output-dir", default="summary",
        help="directory to write summary files (default: summary)")


if __name__ == "__main__":
    main.go(split_summaries, setup_args)
