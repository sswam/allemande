#!/bin/bash -eu
cd "$ALLEMANDE_ROOMS"
month="${1:-$(date +%Y-%m)}"
for file in */usage.$month.log; do
	user=$(dirname "$file")
	echo -n "$user"$'\t'
	<"$file" kut 9 | total
done |
order 2rn
