#!/bin/bash
# dir cmd [arg ...]
# In a directory, do something.
# Makes the directory if it does not exist.
# Example:
#   i /etc wc -l passwd

i() {
	eval "$(ally)"
	. mdcd -- "$1" ; shift
	"$@"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	i "$@"
fi
