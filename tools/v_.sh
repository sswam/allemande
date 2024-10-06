#!/bin/bash
# v-: echo a command to stderr

v-() {
	if [ "$#" -eq 0 ]; then
		return 0
	fi
	out=`
		printf "%s" "${V_PS1:-}"
		printf "%q " "$@"
	`
	printf "%s\n" "${out% }" >&2
}

if [ "$0" = "$BASH_SOURCE" ]; then
	v- "$@"
fi
