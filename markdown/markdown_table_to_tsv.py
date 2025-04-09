#!/usr/bin/env python3-allemande

import re
import sys
import csv
import io

def markdown_table_to_tsv(table_str):
	table_lines = table_str.strip().split('\n')
	headers, *rows = [re.split(r'\s*\|\s*', line.strip('|').strip()) for line in table_lines if line.strip() and not line.startswith('|-')]

	output = io.StringIO()
	writer = csv.writer(output, delimiter='\t')
	writer.writerow(headers)
	writer.writerows(rows)
	tsv_table = output.getvalue()

	return tsv_table

if __name__ == '__main__':
	table_str = sys.stdin.read()
	tsv_table = markdown_table_to_tsv(table_str)
	print(tsv_table)
