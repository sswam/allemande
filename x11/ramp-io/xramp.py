#!/usr/bin/env python3

import sys

import argh
from sh import ramp_gen, ramp_io

def iclamp(x, a, b):
	return max(a, min(x, b))

def ramp_range(f):
	return iclamp(int(f * 65536), 0, 65535)

def xramp(r0=0, r1=1, g0=0, g1=1, b0=0, b1=1):
	r0 = ramp_range(r0)
	r1 = ramp_range(r1)
	g0 = ramp_range(g0)
	g1 = ramp_range(g1)
	b0 = ramp_range(b0)
	b1 = ramp_range(b1)

	ramp_io(_in=ramp_gen(r0, r1, g0, g1, b0, b1))

#	ramp_io(_in=ramp_gen(r0, r1, g0, g1, b0, b1, _piped=True))

#	pipe = subprocess.Popen(['ramp-gen', str(r0), str(r1), str(g0), str(g1), str(b0), str(b1)], stdout=subprocess.PIPE)
#	subprocess.run(['ramp-io'], stdin=pipe.stdout, stdout=subprocess.DEVNULL)

def usage():
	print("""Usage:	xramp [args]
	xramp f			- set all channels to f
	xramp f0 f1		- set all channels to f0, f1
	xramp r1 g1 b1		- set red to r1, green to g1, blue to b1
	xramp r0 r1 g0 g1 b0 b1	- set red to r0, r1, green to g0, g1, blue to b0, b1""")

def main(*args):
	n = len(args)
	if n == 0:
		xramp()
	elif n == 1:
		f, = map(float, args)
		xramp(0, f, 0, f, 0, f)
	elif n == 2:
		f0, f1 = map(float, args)
		xramp(f0, f1, f0, f1, f0, f1)
	elif n == 3:
		r1, g1, b1 = map(float, args)
		xramp(0, r1, 0, g1, 0, b1)
	elif n == 6:
		r0, r1, g0, g1, b0, b1 = map(float, args)
		xramp(r0, r1, g0, g1, b0, b1)
	else:
		usage()
		return 1
	return 0

if __name__ == '__main__':
	sys.exit(main(*sys.argv[1:]))
