#!/bin/bash

model=claude
N=50
delay=1

mkdir -p simple

I=0
for complex in *.md; do
	simple="simple/$complex"
	if [ -s "$simple" ]; then continue; fi
	process -m="$model" "Please simplify this devlog entry for programmers and a general audience,
including some technical details, but a lot less. Follow the style of ref.md please,
but I love this project; don't make it seem like suffering or a burden. Please go right into the devlog entry with no preamble or following text." ref.md <"$complex" >"$simple"
	sleep "$delay"
	I=$((I + 1))
	if [ $I -ge $N ]; then
		break
	fi
done
