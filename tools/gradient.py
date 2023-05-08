#!/usr/bin/env python3
# gradient.py: generate a gradient of colors

import sys
import numpy as np
import re
import argh
from io import StringIO

# https://stackoverflow.com/questions/25668828/how-to-create-a-list-of-colours-in-a-spectrum

def clamp(x, minimum, maximum):
	return max(minimum, min(x, maximum))

def uint8(x):
	return clamp(int(x), 0, 255)

def float_to_uint8(x):
	return uint8(x * 256)

def rgb_to_hex(rgb):
	return '#%02x%02x%02x' % tuple(map(float_to_uint8, rgb))

def hex_to_rgb(hex):
	h = hex.lstrip('#')
	if 3 <= len(h) <= 4:
		a = [h[i]*2 for i in range(3)]
	else:
		a = [h[i:i+2] for i in range(0, len(h), 2)]
	return tuple(int(x, 16) for x in a)

def to_rgb(x):
	if isinstance(x, (tuple, list, np.ndarray)):
		return x
	if x.startswith('#'):
		return hex_to_rgb(x)
	if x.startswith('rgb(') and x.endswith(')'):
		x = x[4:-1]
	if re.match(r'\s*[\d.]+$', x):
		t = float(x)
		if "." not in x:
			t = x / 256
		return (t, t, t)
	if re.match(r'\s*[\d.]+\s*(,\s*[\d.]+\s*){2,3}$', x):
		t = map(float, x.split(','))
		if "." not in x:
			t = [x / 256 for x in t]
		return tuple(t)
	raise ValueError(f"invalid color code: {x}")

def gradient(start, end, steps, out=sys.stdout, css=False):
	if css:
		print(f"\t/* gradient.py --css {start} {end} {steps} */", file=out)

	start, end = map(to_rgb, (start, end))
	steps = 8

	a0, a1 = map(np.array, (start, end))

	for i in range(steps):
		rgb = a0 + (a1 - a0) * i / (steps - 1)
		# convert to rgb hex code
		hexcode = rgb_to_hex(rgb)
		if css:
			name = f'col{i}'
			print(f"\t--{name}: {hexcode};", file=out)
		else:
			print(hexcode, file=out)

def test_gradient():
	start = "#000000"
	end = "rgb(255,255,255)"
	out = StringIO()
	gradient(start, end, 8, out, css=True)
	assert out.getvalue() == """\
	/* gradient.py --css #000000 rgb(255,255,255) 8 */
	--col0: #000000;
	--col1: #242424;
	--col2: #484848;
	--col3: #6d6d6d;
	--col4: #919191;
	--col5: #b6b6b6;
	--col6: #dadada;
	--col7: #ffffff;
"""

if __name__ == '__main__':
	argh.dispatch_command(gradient)
