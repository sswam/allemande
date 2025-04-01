#!/bin/sh
for F; do (
	cd "$(dirname "$F")"
	if [ -d "$F" ]; then
		git add -u "$(basename "$F")"
	else
		git add "$(basename "$F")"
	fi
) done
if [ $# -eq 0 ]; then
	git add -u .
fi
