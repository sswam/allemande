#!/bin/bash -eua
# bb-voice: a simple voice chat program

set -a

if [ ! -e "$file" ]; then
	> "$file"
fi

if [ -n "`amixer sget Capture | grep '\[off\]'`" ]; then
	mic_state=nocap
else
	mic_state=cap
fi

trap "amixer sset Capture $mic_state; pkill -P $$" EXIT

atail.py -f -r -n"${rewind:-0}" "$file" |
get-bot-lines |
filter-speech |
v $speak
