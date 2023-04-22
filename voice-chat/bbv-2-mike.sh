#!/bin/bash -eua
# bb-voice: a simple voice chat program

nt mic

. ./env-work.sh

if [ ! -e "$file" ]; then
	> "$file"
fi

# rm -f /tmp/drop-the-mic

mic_on() { amixer sset Capture cap; }
mic_on

trap "mic_on; pkill -P $$" EXIT

mike.py | tee /dev/stderr | (
while read line; do
	if [ ! -s "$file" -a -n "$mission" ]; then
		printf "%s\n%s:\t%s\n" "$mission" "$user" "$line" >> "$file"
	elif [ -n "$add_prompts" ]; then
		printf "%s:\t%s\n" "$user" "$line" >> "$file"
	else
		printf "%s\n" "$line" >> "$file"
	fi
	while read -t 0.1 line; do
		:
	done || true
done 
)
