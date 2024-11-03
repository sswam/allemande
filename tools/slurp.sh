#!/usr/bin/env bash

# [file]
# Read entire file and output it exactly.
# This can be used to prevent re-reading output when modifying or appending to
# an input file.

slurp() {
	eval "$(ally)"

	local temp_file
	temp_file=$(mktemp "${TMPDIR:-/tmp}/slurp.XXXXXXXX")
	trap 'rm -f "$temp_file"' RETURN

	cat "${1:--}" >"$temp_file"
	cat "$temp_file"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	slurp "$@"
fi

# version: 0.1.4
