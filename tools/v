#!/bin/bash
# v: echo and execute a command

. v-

v() {
	v- "$@"
	"$@"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	v "$@"
fi
