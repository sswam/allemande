#!/bin/bash -eu

# [path...]
# Adds one or more paths to .gitignore, relative to git root

ignore() {
	local v=0	# verbose output

	. opts

	# Get the git root directory
	local git_root=$(git rev-parse --show-toplevel 2>/dev/null)
	if [ $? -ne 0 ]; then
	    echo "Error: Not in a git repository."
	    exit 1
	fi

	for path in "$@"; do
		# Convert path to be relative to git root
		local rel_path=$(realpath --no-symlinks --relative-to="$git_root" "$path")

		# Ensure the path starts with a slash
		rel_path="/${rel_path#/}"

		# Check if the path already exists in .gitignore
		if grep -q "^${rel_path}$" "$git_root/.gitignore" 2>/dev/null; then
			if [ "$f" -eq 0 ]; then
				echo >&2 "Path '$rel_path' already exists in .gitignore."
			fi
		fi

		# Add the path to .gitignore
		printf "%s\n" "$rel_path" >> "$git_root/.gitignore"

		if [ "$v" = 1 ]; then
			echo "Added '$rel_path' to .gitignore"
		fi
	done
}

if [ "$BASH_SOURCE" = "$0" ]; then
	ignore "$@"
fi
