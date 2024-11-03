#!/usr/bin/env bash
# [file ...]
# Commit changes using LLM in xterm windows

messy-xterm() {
	local file=

	eval "$(ally)"

	if [ "$#" = 0 ]; then
		exec xargs-tsv messy-xterm
		exit 120
	fi
	xterm-screen-run ci "$*" messy "$@"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	messy-xterm "$@"
fi

# version: 0.1.1
