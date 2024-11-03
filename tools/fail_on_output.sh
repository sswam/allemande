#!/usr/bin/env bash

# [command] ...
# Run command, fail if it produces any output

fail_on_output() {
	local output
	output=$("$@" 2>&1) || return $?
	if [ -n "$output" ]; then
		printf "%s\n" "$output" >&2
		return 1
	fi
	return 0
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	fail_on_output "$@"
fi

# version: 0.1.0
