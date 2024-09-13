#!/bin/bash -eu

script="$1"
room="$2"
start="${3-}"

if [ -n "$start" ]; then
	< "$script" sed -n "/$start/,\$p" | tail -n +2 > "$script.tmp"
	script="$script.tmp"
fi

> subtitles.txt
tail -f subtitles.txt | script_sync.py "$script" |
grep --line-buffered . | buflines.py 5 10 'Movie on TV:' '	' |
tee -a "$room"
