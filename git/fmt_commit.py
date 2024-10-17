#!/usr/bin/env python3

"""
This module formats git commit messages by adding two spaces before continued lines.
"""

import sys
import logging
from typing import TextIO, Iterable

from ally import main, logs, geput  # type: ignore
from ally.geput import Get, Put, inputs, prints

__version__ = "0.1.2"

logger = logs.get_logger()


def format_commit_message(lines: Iterable[str]) -> list[str]:
	"""Format the commit message by adding two spaces before continued lines."""
	formatted_lines: list[str] = []
	for line in lines:
		if not line.startswith("- ") and formatted_lines and formatted_lines[-1].startswith("- "):
			line = "  " + line
		formatted_lines.append(line)
	return formatted_lines


def fmt_commit(
	get: Get,
	put: Put,
) -> None:
	"""
	Format git commit messages by adding two spaces before continued lines.
	"""
	lines = inputs(get)
	formatted_lines = format_commit_message(lines)
	prints(put, formatted_lines)


if __name__ == "__main__":
	main.go(fmt_commit)

