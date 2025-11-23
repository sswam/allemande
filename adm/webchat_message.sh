#!/usr/bin/env bash

# [options] message
# Append a message to webchat with user info

webchat-message() {
	local user= u=             # user name, defaults to titled $USER
	local room= r="Ally Chat"  # room name, defaults to Ally Chat
	local file= f=             # bb file directly
	local root= R=             # base rooms dir

	eval "$(ally)"

	local message=${1:-}
	if [ -z "$message" ]; then
		die "message required"
	fi

	# Set user to title case of $USER if not specified
	if [ -z "$user" ]; then
		user=${USER^}
	fi

	# Prepend tab to each line of message
	message=$(printf "%s" "$message" | sed 's/^/\t/')

	local target_file
	local root
	if [ -n "$root" ]; then
		root="$root"
	else
		root="$ALLEMANDE_HOME/rooms"
	fi
	if [ -n "$file" ]; then
		target_file="$file"
	else
		target_file="$root/$room.bb"
	fi
	printf "%s:%s\n\n" "$user" "$message" >> "$target_file"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	webchat-message "$@"
fi
