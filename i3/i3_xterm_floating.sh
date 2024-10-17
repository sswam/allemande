#!/bin/bash
# cmd [arg ...]
# Run a command in a floating xterm window in i3

i3-xterm-floating() {
	local term= t="xterm" # terminal emulator to use
	local geom= g="80x24" # geometry of the terminal window
	local hold= H=0       # flag to hold the terminal open
	local title= T=       # title to set for the terminal window
	local wait= w=0       # wait for the terminal to close

	eval "$(ally)"

	local cmd=("$@")

	# Build the command array
	local run_cmd=("$term" "-name" "xterm-floating" "-geometry" "$geom")

	if [[ ${#cmd[@]} -gt 0 ]]; then
		# hold?
		if [ "$hold" -eq 1 ]; then
			run_cmd+=("-hold")
		fi
		if [ -n "$title" ]; then
			run_cmd+=("-T" "$title")
		fi
		run_cmd+=("-e")
		run_cmd+=("${cmd[@]}")
	fi

	# Run the command
	# * not through i3, as it doesn't know my PATH
	"${run_cmd[@]}" &

	# Rely on i3 config: for_window [instance="xterm-floating"] floating enable
#	i3-msg '[instance="xterm-floating"] floating enable, move position center' >/dev/null

	# Wait for the terminal to close
	if [ "$wait" -eq 1 ]; then
		wait
	fi

	# restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	i3-xterm-floating "$@"
fi
