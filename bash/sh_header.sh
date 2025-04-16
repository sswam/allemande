#!/usr/bin/env bash
# Read a line and format as a header with dashes
# Formats a header line with dashes before and after

sh-header() {
	local line

	# Read one line from stdin
	read -r line || return 0

	# Remove any existing header formatting
	line="$(echo "$line" | sed -e 's/^#\s*-*\s*//; s/\s*-*\s*$//')"

	# Add "# " prefix if not present
	line="# -------- ${line#\# } "

	# Pad to 78 characters with dashes, then output
	local padding="$(printf "%*s" $((78 - ${#line})) | tr ' ' '-')"
	printf "%s%s\n" "$line" "$padding"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	sh-header
fi

# version: 0.1.2
