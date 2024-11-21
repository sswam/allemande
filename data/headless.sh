#!/usr/bin/env bash
# command [args]
# Process a table keeping the header in place

headless() {
	eval "$(ally)"

	cmd=("$@")

	# Read the header line
	IFS= read -r header || die "no input"
	printf '%s\n' "$header"

	# Process the rest of the input
	"${cmd[@]}"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	headless "$@"
fi
