#!/bin/bash

# [txt2tsv]
# Convert text to tab-separated values

txt2tsv() {
	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	. opts

	local slurp="$(cat)"

	# Guess columns and get kutc argument
	local kutc_arg=$(echo "$slurp" | guess-columns | tail -n1)

	# Convert to TSV
	echo "$slurp" | kutc "$kutc_arg"

	# restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	txt2tsv "$@"
fi
