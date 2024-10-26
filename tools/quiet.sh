#!/bin/bash
# quiet: suppress output and errors

exec=

quiet() {
	$exec "$@" >/dev/null 2>&1
}

alias q=error-to-output

if [ "$0" = "$BASH_SOURCE" ]; then
	exec=exec
	quiet "$@"
fi
