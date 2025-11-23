#!/usr/bin/env bash

# screen window command [arg ...]
# Run a command in a new screen window and optionally open an xterm

xterm-screen-run() {
	eval "$(ally)"

	local screen=$1
	local window=$2
	shift 2

	exec </dev/tty 2>/dev/null || true
	screen-run "$screen" "$window" "$@"
	if [ -n "${DISPLAY:-}" ]; then
		xterm -e screen -x "$screen" -p "$window" & disown
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	xterm-screen-run "$@"
fi

# version: 0.1.1
