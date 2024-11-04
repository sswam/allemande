#!/bin/bash
#PARALLEL_MAX=${PARALLEL_MAX:-2}
i=0
while read url
do
	name="$(printf "%06d_" $i)$(basename "$url")"
	. para wg "$@" -O="$name" "$url"
	((i++))
done
wait
