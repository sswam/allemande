#!/usr/bin/env bash

# screen window command [arg ...]
# Run a command in a new screen window and optionally open an xterm

xterm-screen-run() {
	eval "$(ally)"

	local screen=$1
	local window=$2
	shift 2

	screen-run "$screen" "$window" "$@" </dev/tty
	if [ -n "$DISPLAY" ]; then
		xterm -e screen -x "$screen" -p "$window" & disown
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	xterm-screen-run "$@"
fi

# version: 0.1.1
