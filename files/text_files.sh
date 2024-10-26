#!/usr/bin/env bash

# Filter a list of files from stdin, output only text files or binary with -v --inverse option

text_files() {
	local inverse= v= # inverse the filter (show binary files)
	local verbose= V= # verbose output

	eval "$(ally)"

	if [ -t 0 ]; then
		[ "$verbose" = 1 ] && echo >&2 "No input provided. Please pipe a list of files."
		return 1
	fi

	while IFS= read -r file; do
		if file --mime-type "$file" | grep -q "text/"; then
			if [ "$inverse" != 1 ]; then
				printf "%s\n" "$file"
			fi
		else
			if [ "$inverse" = 1 ]; then
				printf "%s\n" "$file"
			fi
		fi
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	text_files "$@"
fi

# version: 0.1.1

# TODO: Add support for multiple file patterns
# FIXME: Improve performance for large file sets
# XXX: Consider using `file` command's `-i` option for more accurate MIME type detection

# Based on the task description and the current script, I'll make the necessary changes to `text_files.sh`. Here's the updated version:

# Changes made:
#
# 1. Removed the `file_pattern` argument and related logic.
# 2. Changed the function to read file names from stdin instead of using `find`.
# 3. Removed the `files` array and the `mapfile` command.
# 4. Added a check to see if input is provided via pipe.
# 5. Used a `while` loop to read file names from stdin.
# 6. Bumped the patch version to 0.1.1.
#
# This script now reads a list of files from stdin, one per line, and processes them according to the `-v` (inverse) option. The `-V` (verbose) option is still available but only used for the input check message.
#
# Note that this script assumes that the file names provided via stdin are valid and accessible. You may want to add additional error checking if needed.

