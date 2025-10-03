#!/usr/bin/env bash
# stopwatch
# Simple stopwatch that measures elapsed time until Enter is pressed

stopwatch() {
	local start
	local elapsed

	start=$(date +%s.%N)
	# read raw line
	IFS= read -r line
	printf "%s\n" "$line"
	elapsed=$(echo "$(date +%s.%N) - $start" | bc)
	printf >&2 "Time elapsed: %.3f seconds\n" "$elapsed"
	exec cat
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	stopwatch "$@"
fi

# version: 0.1.1
