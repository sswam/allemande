#!/bin/bash
rooms=$ALLEMANDE_HOME/rooms.server
user=Sam
room=work

mike |
while read message; do
	printf "%s:\t%s\n\n" "$user" "$message"
	v webchat-message -u=$user -f=$rooms/$room "$message"
done
