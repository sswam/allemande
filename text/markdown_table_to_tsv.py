#!/usr/bin/env python3-allemande

import re
import sys
from tabulate import tabulate

def markdown_table_to_tsv(table_str):
	table_lines = table_str.strip().split('\n')
	headers, *rows = [re.split(r'\s*\|\s*', line.strip('|')) for line in table_lines if line.strip() and not line.startswith('|-')]

	tsv_table = tabulate(rows, headers=headers, tablefmt='tsv')
	return tsv_table

if __name__ == '__main__':
	table_str = sys.stdin.read()
	tsv_table = markdown_table_to_tsv(table_str)
	print(tsv_table)
