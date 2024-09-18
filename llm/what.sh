#!/bin/bash -eu
# [prompt]
# Processes "What is this?" queries

process_what() {
	local v=0	# verbosity level
	local m=	# model
	local p=	# extra prompt

	. opts

	local proc="proc"
	if [ "$v" = 1 ]; then
		proc="process"
	fi

	local prompt="What is this?"
	if [ -n "$p" ]; then
		prompt+=", $p"
	fi

	$proc -m="$m" "$prompt $*"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	process_what "$@"
fi
