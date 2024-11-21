#!/usr/bin/env bash

# [message ...]
# Updates status message

status-update() {
	file= f=     # status file path, defaults to ~/my/status.txt
	stdin= i=    # read message from stdin
	notify= n=   # send notification to i3status

	eval "$(ally)"

	# Set default status file if not specified
	file=${file:-~/my/status.txt}

	# Create target directory if it doesn't exist
	mkdir -p "$(dirname "$file")"

	# Read message from stdin if -i or --stdin is specified
	if (( stdin )); then
		IFS= read -r message
	else
		message="$*"
	fi

	# Write status message
	printf "%s\n" "$message" > "$file"

	# Send notification to i3status if -n or --notify is specified
	if (( notify )); then
		killall -s USR1 i3status
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	status-update "$@"
fi

# version: 0.1.0
