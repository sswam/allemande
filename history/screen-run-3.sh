#!/bin/bash -eu

# screen-run: run a command using GNU screen, in a given screen and window

SCREEN_NEW_DELAY="0.1"
SCREEN_NEW_OPTS=""

screen-new-fg() {
	local screen=$1
	screen $SCREEN_NEW_OPTS -U -dRR "$screen"
	wait
}

screen-new-bg() {
	local screen=$1
	(
		sleep $SCREEN_NEW_DELAY
		screen -S "$screen" -X detach
	) &
	screen $SCREEN_NEW_OPTS -U -dRR "$screen"
	wait
}

screen-list() {
	screen -ls | awk -F'[.\t]' '/^\t/ {print $3}'
}

screen-exists() {
	local screen=$1
	local IFS=$'\n'
	for s in $(screen-list); do
		if [ "$s" = "$screen" ]; then
			return 0
		fi
	done
	return 1
}

screen-window-new-fg() {
	local screen=$1 window=$2
	if ! screen-exists "$screen"; then
		(
			sleep $SCREEN_NEW_DELAY
			screen -S "$screen" -X title "$window"
		) &
		screen-new-fg "$screen"
	else
		(
			sleep $SCREEN_NEW_DELAY
			screen -S "$screen" -X screen -t "$window"
		) &
		screen-attach "$screen"
	fi
}

screen-window-new-bg() {
	local screen=$1 window=$2
	if ! screen-exists "$screen"; then
		screen-new-bg "$screen"
		screen -S "$screen" -X title "$window"
	else
		screen -S "$screen" -X screen -t "$window"
	fi
}

# note: this is not used by the main script
screen-window-select() {
	local screen=$1 window=$2
	screen -S "$screen" -X \select "$window"
}

screen-window-kill() {
	local screen=$1 window=$2
	screen -S "$screen" -p "$window" -X kill
}

screen-stuff() {
	local screen=$1 window=$2
	shift 2
	local keys=$*
	screen -S "$screen" -p "$window" -X stuff "$keys"
}

screen-clear-stuff-line() {
	local screen=$1 window=$2
	shift 2
	local keys=$*
	screen-stuff "$screen" "$window" "^L$*^M"
}

screen-run-lines-fg() {
	local screen=$1 window=$2
	shift 2
	(
		sleep $SCREEN_NEW_DELAY
		sleep $SCREEN_NEW_DELAY
		for line; do
			screen-clear-stuff-line "$screen" "$window" "$line"
		done
	) &
	screen-window-new-fg "$screen" "$window"
}

screen-run-lines-bg() {
	local screen=$1 window=$2
	screen-window-new-bg "$screen" "$window"
	for line; do
		screen-clear-stuff-line "$screen" "$window" "$line"
	done
}

screen-attach() {
	local screen=$1 window=${2:-}
	if [ -n "$window" ]; then
		screen -x "$screen" -p "$window"
	else
		screen -x "$screen"
	fi
}

screen-run() {
	background=
	kill=
	config=
	while getopts 'bkc:' opt; do
		case "$opt" in
		b)
			background=1
			;;
		k)
			kill=1
			;;
		c)
			SCREEN_NEW_OPTS="$SCREEN_NEW_OPTS -c $OPTARG"
			;;
		esac
	done
	shift $((OPTIND - 1))

	local screen=$1 window=$2
	shift 2
	line=`printf '%q ' "$@"`
	if [ -n "$kill" ]; then
		screen-window-kill "$screen" "$window"
	fi
	if [ -n "$background" ]; then
		screen-run-lines-bg "$screen" "$window" "${line% }"
	else
		screen-run-lines-fg "$screen" "$window" "${line% }"
	fi
}

if [ "$0" = "$BASH_SOURCE" ]; then
	screen-run "$@"
fi
