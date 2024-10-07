#!/bin/bash -eu

# [path...]
# Adds one or more paths to .gitignore, relative to git root

ignore() {
	local v=0	# verbose output
	local e=	# add to .git/info/exclude

	. opts

	# Get the git root directory
	local git_root=$(git rev-parse --show-toplevel 2>/dev/null)
	if [ $? -ne 0 ]; then
	    echo "Error: Not in a git repository."
	    exit 1
	fi

	if [ "$e" = 1 ]; then
		ignore_file=".git/info/exclude"
	else
		ignore_file=".gitignore"
	fi
	ignore_file="$git_root/$ignore_file"

	for path in "$@"; do
		# Convert path to be relative to git root
		local rel_path=$(realpath --no-symlinks --relative-to="$git_root" "$path")

		# Ensure the path starts with a slash
		rel_path="/${rel_path#/}"

		# Check if the path already exists in .gitignore
		if grep -q "^${rel_path}$" "$ignore_file" 2>/dev/null; then
			if [ "$f" -eq 0 ]; then
				echo >&2 "Path '$rel_path' already exists in $ignore_file"
			fi
		fi

		# Add the path to .gitignore
		printf "%s\n" "$rel_path" >> "$ignore_file"

		if [ "$v" = 1 ]; then
			echo "Added '$rel_path' to $ignore_file"
		fi
	done
}

if [ "$BASH_SOURCE" = "$0" ]; then
	ignore "$@"
fi
