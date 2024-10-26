#!/usr/bin/env bash

# Set ctime of file/s
#
# It tries using ln (hard link) to set ctime.
# If ln fails, e.g. a filesystem that doesn't support hard links,
# it falls back to using mv, or if mv fails (unwritable directory),
# it uses chmod. Which also is not necessarily guaranteed to work.
#
# It's overengineered, but not as much as my original
# attempt which was in Python and attempted to reimplement
# all the functionality of touch(1).
#
# Now it's over-documented too.
#
# Also, it likely does not work for my original purpose of writing it,
# which was to trigger awatch (inotify) without changing mtime.

eval "$(ally)"

for filename; do
	temp_file=$(mktemp -p "$(dirname "$filename")" ".${filename##*/}.XXXXXX")

	if ln "$filename" "$temp_file" 2>/dev/null; then
		rm "$temp_file"
	elif mv "$filename" "$temp_file"; then
		mv -i "$temp_file" "$filename"
	else
		old_mode=$(stat -c %a "$filename")
		chmod 000 "$filename"
		chmod "$old_mode" "$filename"
	fi
done

# version: 0.1.3
