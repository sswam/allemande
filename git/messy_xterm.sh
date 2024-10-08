#!/usr/bin/env bash
# [file ...]
# Commit changes using LLM in xterm windows

messy-xterm() {
	local file=

	eval "$(ally)"

	if [ "$#" = 0 ]; then
		git-mod | xa confirm -t messy-xterm
		exit
	fi
	for file in "$@"; do
		xterm-screen-run ci "$file" messy "$file"
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	messy-xterm "$@"
fi

# version: 0.1.1
