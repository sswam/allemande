#!/usr/bin/env bash
# [options] file command...
# Modify code in file using the specified command.

code-modify() {
	local no_edit= E=0 # do not edit

	# shellcheck disable=SC1091
	eval "$(ally)"

	local file=$1
	shift
	local command=("$@")

	# If no file is provided, process input stream
	if [ -z "$file" ] || [ "$file" = "-" ]; then
		"${command[@]}" | markdown-code -c '#'
		return
	fi

	# Locate the file and create a backup
	file=$(locate_file "$file")
	[ -n "$file" ] || return 1
	backup "$file"

	# Process the file content and save to a temporary file
	<"$file" "${command[@]}" | markdown-code -c '#' >"$file~"

	# Swap the original and processed files
	swapfiles "$file" "$file~"

	# Open both files in vimdiff for comparison
	if [ "$no_edit" = 0 ]; then
		vimdiff "$file" "$file~"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	code-modify "$@"
fi

# version: 0.1.1
