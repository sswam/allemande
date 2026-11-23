#!/usr/bin/env python3-allemande

import sys
from datetime import *
from math import *
from random import *

args = sys.argv[1:]
if args:
	print(eval(' '.join(args)))
else:
	for line in sys.stdin:
		line = line.strip()
		# print(f"[{line}]", file=sys.stderr)
		print(eval(line))
