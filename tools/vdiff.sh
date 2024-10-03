#!/bin/bash -eu
# [file ...]
# Find files and open in vimdiff.

vdiff() {
	eval "$(ally)"
	local files=("$@")
	for i in "${!files[@]}"; do
		files[$i]="$(finder "${files[$i]}")"
	done
	vimdiff "${OPTS_UNKNOWN[@]}" "${files[@]}"
}

if [ "$0" = "${BASH_SOURCE[0]}" ]; then
	vdiff "$@"
fi
