#!/bin/bash
# error-to-output: send stderr to stdout

exec=

error-to-output() {
	$exec "$@" 2>&1
}

alias eo=error-to-output

if [ "$0" = "$BASH_SOURCE" ]; then
	exec=exec
	error-to-output "$@"
fi
