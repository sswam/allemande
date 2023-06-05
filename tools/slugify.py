#!/usr/bin/env python3

import re
import sys

import argh

# TODO convert & to _and_

def slugify(text):
	text = re.sub(r'[^a-zA-Z0-9]', '_', text)
	text = re.sub(r'_+', '_', text)
	text = re.sub(r'^_|_$', '', text)
	return text

def slugify_main(*text):
	if len(text):
		print(slugify(" ".join(text)))
	else:
		for line in sys.stdin:
			print(slugify(line.rstrip("\n")))

if __name__ == "__main__":
	argh.dispatch_command(slugify_main)
