#!/usr/bin/env python3

import re
import sys

from ally import main
from argh import arg

@arg("-u", "--underscore", help="use underscores", dest="hyphen", action="store_false")
@arg("-B", "--no-boolean", help="do not replace & and |", dest="boolean", action="store_false")
def slugify(*text, lower=False, upper=False, hyphen=True, boolean=True) -> str|list[str]:
	if len(text):
		text = " ".join(text)
	else:
		for line in sys.stdin:
			print(slugify(line.rstrip("\n"), lower=lower, upper=upper, hyphen=hyphen))
		return
	if boolean:
		text = re.sub(r'&', '_and_', text)
		text = re.sub(r'\|', '_or_', text)
	text = re.sub(r'[^a-zA-Z0-9]', '_', text)
	text = re.sub(r'_+', '_', text)
	text = re.sub(r'^_|_$', '', text)
	if not text:
		text = "_"
	if lower:
		text = text.lower()
	elif upper:
		text = text.upper()
	if hyphen:
		text = re.sub(r'_', '-', text)
	return text

if __name__ == "__main__":
	main.run(slugify)
