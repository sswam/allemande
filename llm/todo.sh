#!/bin/bash -eu
# [prompt]
# Processes TODOs in the input

process_todos() {
	local v=0	# verbosity level
	local m=	# model
	local p=	# extra prompt

	. opts

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
