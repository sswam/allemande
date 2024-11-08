#!/usr/bin/env python3-allemande
# catpg: concatenate files, with paragraph breaks and section headers
import argparse
import sys
import re
import logging

from pathlib import Path

logger = logging.getLogger(__name__)

def cat_sections(files, out, sep="\n", keep_filenames=False, force=False):
	good = []
	for file in files:
		path = Path(file)
		try:
			with open(file, "r") as f:
				good.append(file)
		except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
			if force:
				logger.warning("Cannot open file, skipping: %r: %r", file, e)
			else:
				raise

	for file in good:
		path = Path(file)

		if keep_filenames:
			name = str(path)
		else:
			name = path.stem
			name = re.sub(r"[-_]+", " ", name)
			name = name.title()

		try:
			with open(file, "r") as f:
				t = f.read()
				if t and t[-1] == "\n":
					t = t[:-1]
				print(f"## {name}\n", file=out)
				print(t, file=out)
				print(sep, file=out, end="")
		except (FileNotFoundError, IsADirectoryError, PermissionError) as e:
			if force:
				logger.warning("Cannot open file, skipping: %r: %r", file, e)
			else:
				raise

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("files", nargs="*", help="list of files to concatenate")
	parser.add_argument("--sep", default="\n\n", help="paragraph break character (default: newline)")
	parser.add_argument("--keep-filenames", "-k", action="store_true", help="don't clean up the filenames in output")
	parser.add_argument("--force", "-f", action="store_true", help="continue even if some files are unreadable")
	args = parser.parse_args()

	cat_sections(args.files, sys.stdout, sep=args.sep, keep_filenames=args.keep_filenames, force=args.force)


if __name__ == "__main__":
	main()
