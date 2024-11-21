#!/usr/bin/env bash
# FILE
# Open file and its backup in vimdiff

vimdiff-tilde() {
	eval "$(ally)"

	[ $# = 1 ] || usage

	local file="$1"

	file="$(realpath "$(which-file "$file")")"

	if [ -z "$file" ]; then
		die "File not found: $1"
	fi

	vimdiff "$file" "$file~"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	vimdiff-tilde "$@"
fi

# version: 0.1.1
