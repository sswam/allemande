#!/bin/bash -eu
# [prompt]
# Processes TODOs, FIXMEs, and XXXs in the input.

process_todos() {
	local v=0	# verbosity level
	local m=	# model

	. opts

	local p="$*"

	local proc="proc"
	if [ "$v" = 1 ]; then
		proc="process"
	fi

	local prompt="Please work on the TODO / FIXME / XXX (only)"
	if [ -n "$p" ]; then
		prompt+=", $p"
	fi
       	prompt+=". Don't strip comments. You can add comments with other suggestions."

	$proc -m="$m" "$prompt"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	process_todos "$@"
fi
