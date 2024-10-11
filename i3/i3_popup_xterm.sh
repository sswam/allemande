#!/bin/bash
# cmd [arg ...]
# Run a command in a floating xterm window in i3

XTERM_OPEN_SLEEP=0.2

i3_popup_xterm() {
	local term= t="xterm"  # terminal emulator to use
	local geom= g="80x24"  # geometry of the terminal window
	local float= F=0        # flag to disable floating mode
	local hold= H=0        # flag to hold the terminal open
	local title= T=         # title to set for the terminal window
	local wait= w=0	 # wait for the terminal to close

	eval "$(ally)"

	local cmd=("$@")

	# Build the command array
	local run_cmd=("$term" "-geometry" "$geom")

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

	# If floating mode is enabled, use i3-msg to make the window floating
	if [[ "$float" -eq 0 ]]; then
		sleep "$XTERM_OPEN_SLEEP"
		i3-msg "floating enable" >/dev/null
	fi

	# Wait for the terminal to close
	if [ "$wait" -eq 1 ]; then
		wait
	fi

	# restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	i3_popup_xterm "$@"
fi
