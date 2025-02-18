#!/bin/bash -eu

# room-rotate: rotate a chat room file
# Usage: room-rotate [room_name]
# If no room name is provided, defaults to "Ally Chat"
# Example: room-rotate "My Room"

# Set the room name, defaulting to "Ally Chat" if not provided
room=${1:-Ally Chat}
# Remove the ALLEMANDE_HOME/rooms/ prefix if present
room=${room#$ALLEMANDE_HOME/rooms/}

# Remove .bb or .html extension if present
room=${room%.bb}
room=${room%.html}

# Set the source file paths
from="$ALLEMANDE_HOME/rooms/$room.bb"
from_html="$ALLEMANDE_HOME/rooms/$room.html"

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

# Find the lowest unused number
i=0
while [ -e "$ALLEMANDE_HOME/rooms/$room-$i.bb" ] || [ -e "$ALLEMANDE_HOME/rooms/$room-$i.html" ]; do
	i=$((i + 1))
done

# Set the destination file paths
to="$ALLEMANDE_HOME/rooms/$room-$i.bb"
to_html="$ALLEMANDE_HOME/rooms/$room-$i.html"

# Move the source files to the destination
mv -n "$from_html" "$to_html"
mv -n "$from" "$to"

# Create empty source files
touch "$from"
touch "$from_html"

# Copy ownership and permissions from the rotated files to the new empty files
chown --reference="$to" "$from"
chmod --reference="$to" "$from"
chown --reference="$to_html" "$from_html"
chmod --reference="$to_html" "$from_html"
