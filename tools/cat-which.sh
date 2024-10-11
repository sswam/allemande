#!/bin/bash
# [file ...]
# cat files on path

eval "$(ally)"

X=0
for A; do
	W=$(which-file "$A")
	if [ -n "$W" ]; then
		cat "$W"
	else
		echo >&2 not found: "$W"
		X=1
	fi
done
exit $X
