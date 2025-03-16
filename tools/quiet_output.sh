#!/bin/bash
# quiet-output: suppress output, but not errors

exec=

quiet-output() {
	$exec "$@" >/dev/null
}

alias qo=quiet-output

if [ "$0" = "$BASH_SOURCE" ]; then
	exec=exec
	quiet-output "$@"
fi
