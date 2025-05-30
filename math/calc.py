#!/usr/bin/env python3-allemande

import sys
from math import *

args = sys.argv[1:]
if args:
	print(eval(' '.join(args)))
else:
	for line in sys.stdin:
		print(eval(line))
