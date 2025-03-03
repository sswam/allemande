#!/bin/bash

# Function to create separator line based on header
create_separator() {
	echo "$1" | sed 's/[^|]/-/g'
}

# Process the input
process_table() {
	# Remove existing separator lines (lines containing only - and |)
	grep -v '^[|-]\+$' |
	# Replace multiple spaces before | with a single tab
	sed 's/  *|/\t|/g' |
	# Process through tsv2txt
	tsv2txt |
	# Add separator lines
	awk '
	NR==1 {
		separator = gensub(/[^|]/, "-", "g", $0);
		print separator;
		print $0;
		print separator;
	}
	NR>1 {
		print $0;
	}
	END {
		print separator;
	}'
}

# Read from stdin and process
process_table
