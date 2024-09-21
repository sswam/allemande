#!/bin/bash

# Run a command in a floating xterm window in i3
set -e -u -o pipefail

i3_popup_xterm() {
	local t="xterm"  # terminal emulator to use
	local g="80x24"  # geometry of the terminal window
	local F=0        # flag to disable floating mode
	local H=0        # flag to hold the terminal open
	local T=         # title to set for the terminal window
	local w=	 # wait for the terminal to close

	. opts

	local cmd=("$@")

	# Build the command array
	local run_cmd=("$t" "-geometry" "$g")

	if [[ ${#cmd[@]} -gt 0 ]]; then
		# hold?
		if [ "$H" -eq 1 ]; then
			run_cmd+=("-hold")
		fi
		if [ -n "$T" ]; then
			run_cmd+=("-T")
			run_cmd+=("$T")
		fi
		run_cmd+=("-e")
		run_cmd+=("${cmd[@]}")
	fi

	# Run the command
	# * not through i3, as it doesn't know my PATH
	"${run_cmd[@]}" &

	# If floating mode is enabled, use i3-msg to make the window floating
	if [[ $F -eq 0 ]]; then
		sleep 0.05
		i3-msg "floating enable" >/dev/null
	fi

	# Wait for the terminal to close
	if [ "$w" -eq 1 ]; then
		wait
	fi
}

if [ "$BASH_SOURCE" = "$0" ]; then
	i3_popup_xterm "$@"
fi
