#!/bin/bash -eua
# bb-voice: a simple voice chat program

if [ ! -e "$file" ]; then
	> "$file"
fi

if [ -n "`amixer sget Capture | grep '\[off\]'`" ]; then
	mic_state=nocap
	echo >&2 warning: microphone is off
else
	mic_state=cap
fi

trap "amixer sset Capture $mic_state; pkill -P $$" EXIT

mike.py -v | tee /dev/stderr |
filter-mike |
(
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
