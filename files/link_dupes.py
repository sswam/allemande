#!/usr/bin/env python3-allemande

"""
Creates hard links between duplicate files, preserving the first occurrence and linking others to it.

Usage:
	... | link_dupes

Input format:
	Groups of filenames, one per line, with blank lines separating groups.
	Each group represents identical files.
"""

import sys
import shlex
import itertools

def readlines(file=sys.stdin):
	"""A generator that yields lines from a file, stripping trailing whitespace."""
	while True:
		line = file.readline()
		if not line:
			break
		line = line.rstrip("\r\n")
		yield line

def eprint(*args, **kwargs):
	"""Prints to stderr."""
	print(*args, **kwargs, file=sys.stderr)

def main():
	print("set -ex")

	# Use itertools.groupby to separate the input into groups based on blank lines.
	# The key `bool(line)` groups consecutive non-empty lines together.
	for is_not_empty, files_group in itertools.groupby(readlines(), key=bool):
		# We only care about the groups of actual filenames (where the key is True).
		if not is_not_empty:
			continue

		first_file = next(files_group)

		print()

		for dup_file in files_group:
			print(shlex.join(["ln", "-f", first_file, dup_file]))

if __name__ == "__main__":
	main()
