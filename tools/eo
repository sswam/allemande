#!/bin/bash
# eo: send stderr to stdout

exec=

eo() {
	$exec "$@" 2>&1
}

if [ "$0" = "$BASH_SOURCE" ]; then
	exec=exec
	eo "$@"
fi
