#!/usr/bin/env bash

# [command]
# Runs a command with no input
# Executes the given command with /dev/null as stdin

no-input() {
	local exec=

	eval "$(ally)"

	if [ "${BASH_SOURCE[0]}" = "$0" ]; then
		exec="exec"
	fi

	$exec "$@" </dev/null
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	no-input "$@"
fi

# version: 0.1.0
