#!/usr/bin/env bash

# Reads stdin into a buffer and outputs it all at once
# Example: slow_command | hold.sh > output.txt

hold() {
	local temp_file
	temp_file=$(mktemp) || die "could not create temp file"

	# Ensure temp file cleanup on exit
	trap 'rm -f "$temp_file"' EXIT

	# Read all input into temp file
	cat > "$temp_file" || die "failed to read input"

	# Output everything at once
	cat "$temp_file" || die "failed to output buffer"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	hold "$@"
fi
