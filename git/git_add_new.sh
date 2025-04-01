#!/bin/sh
for F; do
	(
	cd "$(dirname "$F")"
	git add -A "$(basename "$F")"
	)
done
if [ $# -eq 0 ]; then
	git add -A .
fi

