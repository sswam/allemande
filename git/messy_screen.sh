#!/usr/bin/env bash
# [file ...]
# Commit changes using LLM in screen windows

# With no arguments, it commits batches of tab-separated file names from stdin.

messy-screen() {
	local no_connect= X=  # do not connect to the screen

	eval "$(ally)"

	if [ "$#" = 0 ]; then
		exec xargs-tsv messy-screen -X
		screen -c xi </dev/tty
		exit 120
	fi
	screen-run ci "$*" messy "$@" </dev/tty
	if ! ((no_connect)); then
		screen -x ci </dev/tty
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	messy-screen "$@"
fi

# version: 0.1.1
