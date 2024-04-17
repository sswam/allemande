#!/usr/bin/env python3
""" json2csv: convert an array of objects to a CSV file """

import sys
import json
import csv

def main():
	"""
	Main function which converts JSON to CSV.
	It takes JSON from stdin, extracts the field names then writes to CSV via stdout.
	"""
	# Load JSON from stdin
	data = json.load(sys.stdin)

	# Collect field names from all items
	fieldnames = list(dict.fromkeys(k for item in data for k in item))

	# Create CSV writer that writes to stdout
	writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
	writer.writeheader()

	# Write each item in the JSON array as a row in the CSV
	for item in data:
		writer.writerow(item)

if __name__ == "__main__":
	main()
