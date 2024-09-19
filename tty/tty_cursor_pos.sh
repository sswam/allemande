#!/bin/bash -eu
#
# Gets the current cursor position in the terminal

tty_cursor_pos() {
	local timeout=0.1  # Timeout in seconds
	local suffix=""

	. opts

	# Save current terminal settings
	local old_settings=$(stty -g)

	# Set terminal to raw mode
	stty raw -echo

	# Send the cursor position request
	printf "\033[6n"

	# Read the response
	local response=""
	local char
	while true; do
		if char="" && read -r -t "$timeout" -n 1 char; then
			response+="$char"
			if [[ $char == "R" ]]; then
				break
			fi
		else
			stty "$old_settings"
			echo "Error: Timeout while reading terminal response" >&2
			return 1
		fi
	done

	# Restore original terminal settings
	stty "$old_settings"

	# Parse the response
	if [[ ! $response =~ \[([0-9]+)\;([0-9]+)R$ ]]; then
		echo "Error: Invalid response: $response" | cat -v >&2
		return 1
	fi

	local _row=${BASH_REMATCH[1]}
	local _col=${BASH_REMATCH[2]}

	eval "row$suffix=$_row col$suffix=$_col"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	get_terminal_position "$@"
fi
