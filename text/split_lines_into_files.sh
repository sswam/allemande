#!/usr/bin/env bash

# <format> <start>
# Split lines from input file into files using format and sequential numbers

split-lines-into-files() {
	eval "$(ally)"

	local format=$1
	local start=${2:-1}

	local i=$start
	while IFS= read -r line; do
		printf "%s\n" "$line" > "$(printf "$format" "$i")"
		i=$((i + 1))
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	split-lines-into-files "$@"
fi

