#!/usr/bin/env bash

# [interval [count]]
# Watch a command repeatedly

wat() {
	clear= c=       # clear screen before each execution
	interval= s=1   # seconds between executions
	count= i=       # number of executions (unlimited if not set)
	error= e=0      # exit on error
	no_newline= n=  # suppress newline after command output

	eval "$(ally)"

	[ $# -eq 0 ] && return 0

	command=("$@")

	local newline=$'\n'
	if [ "$no_newline" = 1 ]; then
		newline=' '
	fi

	local i=0
	while true; do
		[ "$clear" = 1 ] && clear

		if ! output=$("${command[@]}"); then
			error=1
		fi
		printf "%s%s" "$output" "$newline"
		if [ "$error" = 1 ]; then
			break
		fi
		sleep "$interval"
		i=$((i + 1))
		[ -n "$count" ] && [ "$i" -eq "$count" ] && break
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	wat "$@"
fi

# version: 0.1.1
