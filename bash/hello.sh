#!/bin/bash -eu
# hello.sh:	Hello, world

hello() {
	local who=${1:-world}
	echo "Hello, $who"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	hello "$@"
fi
