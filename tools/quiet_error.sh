#!/bin/bash
# quiet error: suppress errors

exec=

quiet-error() {
	$exec "$@" 2>/dev/null
}

alias qe=quiet-error

if [ "$0" = "$BASH_SOURCE" ]; then
	exec=exec
	quiet-error "$@"
fi
