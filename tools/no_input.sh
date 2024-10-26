#!/bin/bash
# no-input: no input

exec=

no-input() {
	$exec "$@" </dev/null
}

if [ "$0" = "$BASH_SOURCE" ]; then
	exec=exec
	no-input "$@"
fi
