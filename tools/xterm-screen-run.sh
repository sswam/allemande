#!/bin/bash
screen=$1
window=$2
shift 2
screen-run.sh "$screen" "$window" "$@"
xterm -e screen -x "$screen" -p "$window" & disown
