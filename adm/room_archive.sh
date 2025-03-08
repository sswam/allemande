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

# Check if the source file exists
if [ ! -f "$from" ]; then
	echo "No such file: $from" >&2
	exit 0
fi

# Check if the source file is empty
if [ ! -s "$from" ]; then
	echo "Empty file: $from" >&2
	exit 0
fi

to=$(archive -D html "$from")

# Create empty source file and html file, or from template
if [ -e "$from.base" ]; then
	cp "$from.base" "$from"
else
	touch "$from"
fi

# Copy ownership and permissions from the archived file to the new empty file
chown --reference="$to" "$from"
chmod --reference="$to" "$from"
