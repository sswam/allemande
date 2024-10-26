#!/usr/bin/env bash

# [file]
# Creates a backup of the specified file

backup() {
	eval "$(ally)"

	file="$1"

	backup_file="${file}~"

	# Check if backup file exists, and move it to rubbish if it does
	if [ -e "$backup_file" ]; then
		rubbish "$backup_file"
	fi

	# Copy the file to create a backup, overwriting if it exists
	cp -f "$file" "$backup_file"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	backup "$@"
fi

# version: 0.1.0
