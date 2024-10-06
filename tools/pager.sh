#!/bin/bash -eu

n=200	# number of lines per page
o=20	# overlap

. opts

input="$1"
shift
cmd=("$@")

lines=`wc -l < "$input"`

i=1

while true; do
	< "$input" tail -n +$i | head -n $n | "${cmd[@]}"
	if [ $(($i+$n - 1)) -ge $lines ]; then
		break
	fi
	i=$((i+n-o))
done
