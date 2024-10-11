#!/bin/bash
# [file ...]
# ls -l files on path
eval "$(ally)"
for A; do
	W=$(which-file "$A")
	if [ -n "$W" ]; then
		ls --color=auto -l "$W"
	else
		echo >&2 not found
		exit 1
	fi
done
