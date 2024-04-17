#!/bin/bash
# in directory, do something

i() {
	. mdcd -- "$1" ; shift
	"$@"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	i "$@"
fi
