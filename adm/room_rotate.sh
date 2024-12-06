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
	exit 1
fi

# Check if the source file is empty
if [ ! -s "$from" ]; then
	echo "Empty file: $from" >&2
	exit 0
fi

# Set the destination directory
dir="$ALLEMANDE_HOME/rooms/$room/"

# Get the modification time of the source file and format it as a date
secs=`stat -c %Y "$from"`
date=`date +%Y%m%d -d "@$secs"`

# Set the destination file paths
to="$dir/$date.bb"
to_html="$dir/$date.html"

# If destination files already exist, use a timestamp in the filename
if [ -e "$to" -o -e "$to" ]; then
	timestamp=`date +%Y%m%d%H%M%S -d "@$secs"`
	to="$dir/$timestamp.bb"
	to_html="$dir/$timestamp.html"
fi

# Check again if the destination files exist
if [ -e "$to" -o -e "$to" ]; then
	echo "File exists: $to" >&2
	exit 1
fi

# Create the destination directory if it doesn't exist
mkdir -p "$dir"

# Move the source files to the destination
mv -n "$from_html" "$to_html"
mv -n "$from" "$to"
# sleep 1
# mv -n "$to_html.orig" "$to_html"
# rm -f "$to_html.orig"

# Create empty source files
touch "$from"
touch "$from_html"

# Copy ownership and permissions from the rotated files to the new empty files
chown --reference="$to" "$from"
chmod --reference="$to" "$from"
chown --reference="$to_html" "$from_html"
chmod --reference="$to_html" "$from_html"
