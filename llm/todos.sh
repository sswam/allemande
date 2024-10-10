#!/bin/bash -eu
# [prompt]
# Processes TODOs, FIXMEs, and XXXs in the input.

process_todos() {
	local verbose= v=0	# verbosity level
	local model= m=	# model

	eval "$(ally)"

	local prompt="$*"

	local proc="proc"
	if [ "$verbose" = 1 ]; then
		proc="process"
	fi

	local prompt="Please work on the TODO / FIXME / XXX (only)"
	if [ -n "$prompt" ]; then
		prompt+=", $prompt"
	fi
       	prompt+=". Don't strip comments. You can add comments with other suggestions."

	$proc -m="$model" "$prompt"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	process_todos "$@"
fi
