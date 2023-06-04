#!/usr/bin/env python3

import re
import sys

import argh

def slugify_filter(text):
	text = re.sub(r'[^a-zA-Z0-9]', '_', text)
	text = re.sub(r'_+', '_', text)
	text = re.sub(r'^_|_$', '', text)
	return text

def slugify(*text):
	if text is not None:
		print(slugify_filter(" ".join(text)))
	else:
		for line in sys.stdin:
			print(slugify_filter(line.rstrip("\n")))

if __name__ == "__main__":
	argh.dispatch_command(slugify)
