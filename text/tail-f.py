#!/usr/bin/env python3
""" tail-f.py : a program like tail -f that doesn't rewind if the file size shrinks """

import os
import time
import argh
import sys
import sh

def tail_f_n0(filename, n=0, interval=1.0):
	if n > 0:
		sh.tail(filename, n=n, _out=sys.stdout, _err=sys.stderr)
	file_pos = None
	while True:
		try:
			with open(filename, 'r') as f:
				if file_pos is None or file_pos > os.path.getsize(filename):
					f.seek(0, os.SEEK_END)
				else:
					f.seek(file_pos)
				new_lines = f.readlines()
				if new_lines:
					print(''.join(new_lines), end='')
					sys.stdout.flush()
				file_pos = f.tell()

		except FileNotFoundError:
			pass

		time.sleep(interval)

if __name__ == "__main__":
	argh.dispatch_command(tail_f_n0)
