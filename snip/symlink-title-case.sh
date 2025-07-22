#!/usr/bin/env bash

# [filenames]
# Creates title-case symlinks for filenames from stdin

symlink-title-case() {
	while IFS= read -r filename; do
		# Convert first char to uppercase
		title="${filename^}"
		ln -sT "$filename" "$title"
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	symlink-title-case
fi

# version: 0.1.0
