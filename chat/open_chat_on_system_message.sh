#!/bin/bash -eu
# Follows a room's chat and opens the chat in chrome when a system message is seen,
# i.e. when an AI initiates a conversation.
room=$1
atail -p 1 -n 0 -f -w --restart ~/allemande/rooms.server/$room.bb |
while read A; do
	if [[ "$A" = System:* ]]; then
		chrome --new-window "https://chat.allemande.ai/#$room"
	fi
done
