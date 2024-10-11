#!/usr/bin/env bash

# [path ...]
# List files and show targets for symbolic links

for arg; do
	ls "$arg" |
	while IFS= read -r file; do
		if [ -d "$arg" ]; then
			path="$arg/$file"
		else
			path="$file"
		fi
		if [ -L "$path" ]; then
			printf "%s\t%s\n" "$file" "$(readlink "$path")"
		else
			printf "%s\n" "$file"
		fi
	done
done

# version: 0.1.2
