#!/usr/bin/env bash

# [options] message
# Append a message to webchat with user info

webchat-message() {
	local user= u=             # user name, defaults to titled $USER
	local room= r="Ally Chat"  # room name, defaults to Ally Chat

	eval "$(ally)"

	local message=${1:-}
	if [ -z "$message" ]; then
		die "message required"
	fi

	# Set user to title case of $USER if not specified
	if [ -z "$user" ]; then
		user=${USER~}
	fi

	# Prepend tab to each line of message
	message=$(printf "%s" "$message" | sed 's/^/\t/')

	printf "%s:%s\n\n" "$user" "$message" >> "$ALLEMANDE_HOME/rooms/$room.bb"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	webchat-message "$@"
fi
