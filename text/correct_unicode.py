#!/usr/bin/env python3

# clean-stream.py - clean a stream of unicode characters

import sys
import io

def clean_stream(stream):
	for line in stream.buffer:
		yield line.decode('utf-8', 'ignore').rstrip('\n')

def main():
	for line in clean_stream(sys.stdin):
		print(line)

if __name__ == '__main__':
	main()
