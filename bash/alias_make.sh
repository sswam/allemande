#!/usr/bin/env bash
# [directories or files...]
# Generate shell alias functions for non-executable files

alias-make() {
	eval "$(ally)"

	local paths=("$@")

	# Default to current directory if no arguments
	if [ "${#paths[@]}" -eq 0 ]; then
		paths=(.)
	fi

	# Find all non-executable files, following symlinks.
	# Excludes hidden files and directories.
	find -L "${paths[@]}" \
		-name '.*' -prune -o \
		-type f ! -executable -print |
		while IFS= read -r filepath; do
			local basename
			basename=$(basename "$filepath")
			printf '%s() { . %s ; }\n' "$basename" "$filepath"
		done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	alias-make "$@"
fi

# version: 0.1.0
