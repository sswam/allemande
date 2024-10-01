#!/bin/bash -eu
# [prompt]
# Explain like I'm five.

eli5() {
	local v=1	# verbosity level
	local m=	# model
	local p=	# extra prompt

	. opts

	local proc="proc"
	if [ "$v" = 1 ]; then
		proc="process"
	fi

	local prompt="What is this? Please ELI5 every detail, espeically the parts that are not very obvious. Don't omit to explain anything even if it's 'advanced' or whatever. I'm not really five, after all."
	if [ -n "$p" ]; then
		prompt+=", $p"
	fi

	$proc -m="$m" "$prompt $*"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	eli5 "$@"
fi
