#!/bin/bash
for A; do
	W=`wich $A`
	if [ -n "$W" ]; then
		ls --color=auto -l "$W"
	else
		echo >&2 not found
		exit 1
	fi
done
