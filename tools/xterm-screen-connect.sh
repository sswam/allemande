#!/bin/bash
screen=$1
window=$2
shift 2
if [ -n "$DISPLAY" ]; then
	xterm -e screen -x "$screen" -p "$window" & disown
fi
