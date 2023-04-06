#!/usr/bin/env python3 
# strip-lines.py - remove leading and trailing whitespace from each line of an input stream

import sys

def strip_lines(stream):
	for line in stream:
		print(line.strip())

def main():
	strip_lines(sys.stdin)

if __name__ == '__main__':
	main()
