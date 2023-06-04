#!/bin/bash
# qe: quiet stderr

exec=

qe() {
	$exec "$@" 2>/dev/null
}

if [ "$0" = "$BASH_SOURCE" ]; then
	exec=exec
	qe "$@"
fi
