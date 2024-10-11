#!/bin/bash
# [prompt]
# Processes fixes in the input

apply_fixes() {
	local verbose= v=0	# verbosity level
	local model= m=	# model

	eval "$(ally)"

	local prompt="${1:-}"
	shift || true
	local references=("$@")

	local proc="proc"
	if [ "$verbose" = 1 ]; then
		proc="process"
	fi

	local prompt="Please fix this. $prompt"
	prompt+=". Don't strip code comments."
	if [ "${references[*]}" ]; then
		prompt+=" Refer to ${references[*]}."
	fi

	cat-named - "${references[@]}" | $proc -m="$model" "$prompt"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	apply_fixes "$@"
fi
