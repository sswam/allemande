#!/bin/bash -eu
# llm-chat:	chat with an LLM in an editor

p=	# prompt
P=	# prompt, preformatted
	# with system: user: assistant:
m=$ALLEMANDE_LLM_DEFAULT	# model
f=	# prompt file
q=	# don't warn

# example: llm-chat -p=$'system: let's have a cool human chat\nuser:' -m=c

. opts

file="${1:-}"

# warn if file does not end in .chat
if [ -z "$q" -a -n "$file" -a "${file##*.}" != "chat" ]; then
	printf "%s\n" "llm-chat: warning: file does not end in .chat" >&2
	sleep 1
fi

if [ -n "$f" ]; then
	cat "$f" >> "$file"
fi
if [ -n "$p" ]; then
	printf "system: %s\nuser:" "$p" >> "$file"
elif [ -n "$P" ]; then
	printf "system: %s\nuser:" "$p" >> "$file"
fi

# still doesn't exist?  create it
if [ ! -e "$file" ]; then
	touch "$file"
fi

v q llm-loop -m=$m &
P=$!
trap "kill $P" EXIT

"$EDITOR" "$file"
