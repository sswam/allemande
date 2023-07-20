#!/bin/bash
X=0
for A; do
	W=`wich $A`
	if [ -n "$W" ]; then
		cat "$W"
	else
		echo >&2 not found: "$W"
		X=1
	fi
done
exit $X
