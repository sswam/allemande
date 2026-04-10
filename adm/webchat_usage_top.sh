#!/bin/bash -eu
cd "$ALLEMANDE_ROOMS"
month="${1:-$(date +%Y-%m)}"
list=$(
	for file in */usage.$month.log $ALLEMANDE_HOME/usage_unknown.$month.log; do
		user=$(dirname "$file")
		echo -n "$user"$'\t'
		<"$file" kut 9 | total
	done |
	order 2rn
)
(
	printf "%s" "$list" | wc -l
	printf "%s" "$list" | kut 2 | total
	printf "%s" "$list"
) | less
