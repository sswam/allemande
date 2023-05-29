#!/bin/bash
# xtrem-screen-run.sh: run a command in a new screen window
screen=$1
window=$2
shift 2
screen-run.sh "$screen" "$window" "$@"
if [ -n "$DISPLAY" ]; then
	v xterm -e screen -x "$screen" -p "$window" & disown
fi
