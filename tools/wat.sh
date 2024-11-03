#!/usr/bin/env bash

# [interval [count]]
# Watch a command repeatedly

wat() {
	clear= c=        # clear screen before each execution
	interval= s=1    # seconds between executions
	count= n=        # number of executions (unlimited if not set)

	eval "$(ally)"

	[ $# -eq 0 ] && return 0

	local i=0
	while true; do
		[ "$clear" = 1 ] && clear
		"$@"
		sleep "$interval"
		i=$((i + 1))
		[ -n "$count" ] && [ "$i" -eq "$count" ] && break
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	wat "$@"
fi

# version: 0.1.0
