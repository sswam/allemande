#!/bin/bash -eu
# [prompt]
# Processes TODOs in the input

process_todos() {
	local v=0	# verbosity level
	local m=	# model

	. opts

	local p="$*"

	local proc="proc"
	if [ "$v" = 1 ]; then
		proc="process"
	fi

	local prompt="Please do the TODOs"
	if [ -n "$p" ]; then
		prompt+=", $p"
	fi

	$proc -m="$m" "$prompt"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	process_todos "$@"
fi
