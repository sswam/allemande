#!/bin/bash -eu

# room-archive: archive a chat room file
# Usage: room-archive [room_name]
# If no room name is provided, defaults to "Ally Chat"
# Example: room-archive "My Room"

# Set the room name, defaulting to "Ally Chat" if not provided
room=${1:-Ally Chat}
# Remove the ALLEMANDE_HOME/rooms/ prefix if present
room=${room#$ALLEMANDE_HOME/rooms/}

# Remove .bb extension if present
room=${room%.bb}

# Set the source file paths
from="$ALLEMANDE_HOME/rooms/$room.bb"
dirname="$(dirname "$from")"
basename="$(basename "$from")"

if [ ! -f "$from" ]; then
	echo "No such file: $from" >&2
elif [ ! -s "$from" ]; then
	echo "Empty file: $from" >&2
	rm "$from"
else
	to=$(archive -D html "$from")
fi

sleep 0.1

# Create empty source file and html file, or from template
# The template can be foo.base or .foo.base
if [ -e "$from.base" ]; then
	cp "$from.base" "$from"
elif [ -e "$dirname/.$basename.base" ]; then
	cp "$dirname/.$basename.base" "$from"
else
	touch "$from"
fi

# Copy ownership and permissions from the archived file to the new file
if [ -e "$to" ]; then
	chown --reference="$to" "$from"
	chmod --reference="$to" "$from"
fi
