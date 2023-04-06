#!/usr/bin/env python3
# catpg: concatenate files, with paragraph breaks and section headers
import argparse
import sys
import re

from pathlib import Path

def cat_sections(files, out, sep="\n", keep_filenames=False):
	for a in files:
		path = Path(a)
		name = path.stem

		if not keep_filenames:
			name = re.sub(r"[-_]+", " ", name)
			name = name.title()

		print(f"## {name}\n", file=out)
		with open(a, "r") as f:
			t = f.read()
			if t and t[-1] == "\n":
				t = t[:-1]
			print(t, file=out)

		print(sep, file=out, end="")

def main():
	parser = argparse.ArgumentParser()
	parser.add_argument("files", nargs="*", help="list of files to concatenate")
	parser.add_argument("--sep", default="\n\n", help="paragraph break character (default: newline)")
	parser.add_argument("--keep-filenames", "-k", action="store_true", help="don't clean up the filenames in output")
	args = parser.parse_args()

	cat_sections(args.files, sys.stdout, sep=args.sep, keep_filenames=args.keep_filenames)


if __name__ == "__main__":
	main()
