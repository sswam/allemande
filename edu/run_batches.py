#!/usr/bin/env python3-allemande

"""
Process input in batches and run a command for each batch.
"""

import sys
import subprocess
from typing import TextIO
import re

from argh import arg
from ally import main

__version__ = "0.1.1"

logger = main.get_logger()


def extract_items(content: str) -> list[str]:
    """Extract items starting with '# <number>. <heading>' from the content."""
    pattern = r'# \d+\. .*?(?=# \d+\.|$)'
    items = re.findall(pattern, content, re.DOTALL)
    return [item.strip() for item in items]


def process_batches(items: list[str], batch_size: int, command_line: list[str], output: TextIO) -> None:
    """Process items in batches and run the command for each batch."""
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]
        batch_content = "\n\n".join(batch) + "\n"

        try:
            result = subprocess.run(command_line, input=batch_content, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

            if result.stderr:
                print(result.stderr, file=sys.stderr, end='')

            print(result.stdout, file=output, end='')
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e}")
            print(e.stderr, file=sys.stderr, end='')
            raise ValueError("Command failed")


@arg("command", help="command to run for each batch")
@arg("args", nargs="*", help="arguments for the command")
@arg("-n", "--batch-size", type=int, default=3, help="number of items per batch")
def run_batches(
    command: str,
    args: list[str],
    input: TextIO = sys.stdin,
    output: TextIO = sys.stdout,
    batch_size: int = 3,
) -> None:
    """
    Process input in batches and run a command for each batch.
    """
    content = input.read()
    items = extract_items(content)

    process_batches(items, batch_size, [command] + args, output)


if __name__ == "__main__":
    main.run(run_batches)
