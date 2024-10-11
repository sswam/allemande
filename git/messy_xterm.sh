#!/usr/bin/env bash
# [file ...]
# Commit changes using LLM in xterm windows

messy-xterm() {
	local file=

	eval "$(ally)"

	if [ "$#" = 0 ]; then
		xargs-tsv messy-xterm
#		git-mod | xa confirm -t messy-xterm
		exit
	fi
	xterm-screen-run ci "$*" exec messy "$@"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	messy-xterm "$@"
fi

# version: 0.1.1
