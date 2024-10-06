#!/bin/bash
# qo: quiet stdout

exec=

qo() {
	$exec "$@" >/dev/null
}

if [ "$0" = "$BASH_SOURCE" ]; then
	exec=exec
	qo "$@"
fi
