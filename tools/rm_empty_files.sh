#!/bin/bash
# rm-empty-files: remove empty files
find . -type f -size 0 | 
while read -r file; do
	# check that the file is not open
	if ! lsof "$file" >/dev/null 2>&1; then
		rm "$file"
	fi
done
