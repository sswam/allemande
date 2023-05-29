#!/usr/bin/env python3
# read_html_tables.py: read html tables and output as tab-separated text
# this read_html_tables script is in the public domain
# Sam Watkins, 2012

import sys
from os import path, getenv
import argh

from l import *
import ucm_html

@argh.arg('--keep-tags', '-k', nargs='*', type=str, help='tags to keep')
@argh.arg('--select', '-s', nargs='*', type=int, help='select tables to output')
def html_tables_read(keep_tags=None, select=None):
	init(__file__)
	raw_html = sys.stdin.read()
	tables, raw_tables = ucm_html.parse_tables(raw_html, keep_tags=keep_tags)
	n = len(tables)
	warn("number of tables: %d" % n)
	for i in range(0, n):
		if select is None or i in select:
			t = tables[i]
			warn("Table %d:" % i)
			for r in t:
				print('\t'.join(r))
			print()

if __name__ == '__main__':
	argh.dispatch_command(html_tables_read)
