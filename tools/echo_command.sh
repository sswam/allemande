#!/bin/bash
# [cmd args ...]
# echo a command to stderr

echo-command() {
	if [ "$#" -eq 0 ]; then
		return 0
	fi
	out=`
		printf "%s" "${V_PS1:-}"
		printf "%q " "$@"
	`
	printf "%s\n" "${out% }" >&2
}

alias v-=echo-command

if [ "$0" = "$BASH_SOURCE" ]; then
	echo-command "$@"
fi
