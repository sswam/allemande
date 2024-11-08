#!/usr/bin/env python3-allemande
# ts2markdown.py - Convert a TSV file to a Markdown table

import sys

def main():
	"""Main program"""
	# Read the TSV file
	tsv_data = sys.stdin.read()

	# Split the TSV data into lines
	tsv_lines = tsv_data.splitlines()

	# Split the lines into columns
	tsv_columns = [line.split("\t") for line in tsv_lines]

	# Create a Markdown table
	markdown_table = "| " + " | ".join(tsv_columns[0]) + " |\n"
	markdown_table += "| " + " | ".join(["---"] * len(tsv_columns[0])) + " |\n"
	for row in tsv_columns[1:]:
		markdown_table += "| " + " | ".join(row) + " |\n"

	# Print the Markdown table
	print(markdown_table, end="")

if __name__ == "__main__":
	main()
