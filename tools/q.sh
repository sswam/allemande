#!/bin/bash
# q: quiet

exec=

q() {
	$exec "$@" >/dev/null 2>&1
}

if [ "$0" = "$BASH_SOURCE" ]; then
	exec=exec
	q "$@"
fi
