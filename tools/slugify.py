#!/usr/bin/env python3

import re
import sys

import argh

# TODO convert & to _and_

def slugify(text, lower=False, upper=False, hyphen=False):
	text = re.sub(r'[^a-zA-Z0-9]', '_', text)
	text = re.sub(r'_+', '_', text)
	text = re.sub(r'^_|_$', '', text)
	if lower:
		text = text.lower()
	elif upper:
		text = text.upper()
	if hyphen:
		text = re.sub(r'_', '-', text)
	return text

@argh.arg("-H", "--hyphen", help="convert underscores to hyphens", action="store_true")
def slugify_main(*text, lower=False, upper=False, hyphen=False):
	if len(text):
		print(slugify(" ".join(text), lower=lower, upper=upper, hyphen=hyphen))
	else:
		for line in sys.stdin:
			print(slugify(line.rstrip("\n"), lower=lower, upper=upper, hyphen=hyphen))

if __name__ == "__main__":
	argh.dispatch_command(slugify_main)
