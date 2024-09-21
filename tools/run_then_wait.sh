#!/bin/bash

# [command] [-t seconds]
# Runs a command and then waits, optionally for a specified time

run_then_wait() {
	local t=    # wait time in seconds (optional)

	. opts

	local command=( "${@:-}" )

	# Run the specified command
	if [ "${#command[@]}" -gt 0 ]; then
		"${command[@]}"
	fi

	# Wait logic
	if [ -n "$t" ]; then
		read -rt "$t" || true
	else
		read -r
	fi
}

if [ "$BASH_SOURCE" = "$0" ]; then
	set -e -u -o pipefail
	run_then_wait "$@"
fi
