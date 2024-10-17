#!/usr/bin/env python3

"""
Highlight matches in different colors.
"""

import sys
import re
from typing import TextIO

import colorama
from colorama import Fore, Style

from ally import main, logs  # type: ignore

__version__ = "1.0.3"

logger = logs.get_logger()


def color_text(text: str, color: str) -> str:
	color_map = {
		"red": Fore.RED,
		"green": Fore.GREEN,
		"blue": Fore.BLUE,
		"yellow": Fore.YELLOW,
		"magenta": Fore.MAGENTA,
		"cyan": Fore.CYAN,
	}
	return f"{color_map.get(color.lower(), '')}{text}{Style.RESET_ALL}"


def highlight(
	istream: TextIO,
	ostream: TextIO,
	patterns: list[str],
	colors: list[str],
	word_regexp: bool,
):
	colorama.init(autoreset=True)

	for line in istream:
		output_line = line
		matches: list[tuple[int, int, int]] = []

		# Find all matches for all patterns
		for i, pattern in enumerate(patterns):
			if word_regexp:
				pattern = r"\b(" + pattern + r")\b"
			matches.extend((m.start(), m.end(), i) for m in re.finditer(pattern, line))

		# Sort matches by start position
		matches.sort(key=lambda x: x[0])

		# Apply coloring
		if matches:
			new_line = []
			last_end = 0
			for start, end, i in matches:
				new_line.append(output_line[last_end:start])
				color = colors[i]
				new_line.append(color_text(output_line[start:end], color))
				last_end = end
			new_line.append(output_line[last_end:])
			output_line = "".join(new_line)

		ostream.write(output_line)


def highlight_main(
	*patterns: str,
	istream: TextIO = sys.stdin,
	ostream: TextIO = sys.stdout,
	word_regexp: bool = False,
):
	"""
	Highlight matches in different colors.

	Supported colors are:
	red, green, blue, yellow, magenta, cyan

	Examples:
	highlight.py 'blo*d' red 'pla*nts' green 'colou?r' magenta
	highlight.py --word-regexp 'blood' red 'plants' green
	highlight.py 'error' red | less -R
	"""
	if len(patterns) % 2 != 0:
		raise ValueError("Each pattern must have a corresponding color")

	search_patterns = patterns[::2]
	colors = patterns[1::2]

	highlight(istream, ostream, search_patterns, colors, word_regexp)


def setup_args(arg):
	"""Set up the command-line arguments."""
	arg("patterns", nargs="*", help="Patterns to search for and their colors")
	arg("--word-regexp", "-w", help="Match whole words only")
	arg("--istream", help="Input stream")
	arg("--ostream", help="Output stream")


if __name__ == "__main__":
	main.go(highlight_main, setup_args)
