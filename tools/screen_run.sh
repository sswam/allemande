#!/usr/bin/env bash

# [options] screen window command [arg ...]
# Run a command using GNU screen, in a given screen and window

screen-run() {
	local kill= k=	# Kill the existing window before running the command
	local config= c=	# Use a different screenrc file

	eval "$(ally)"	# magic options parser and more

	local SCREEN_NEW_DELAY_1="0.0001"
	local SCREEN_NEW_DELAY_2="1"
	local SCREEN_NEW_OPTS=""
	local FLOCK_WAIT=5

	if [ -n "$config" ]; then
		SCREEN_NEW_OPTS="$SCREEN_NEW_OPTS -c $config"
	fi

	local screen=$1 window=$2
	shift 2
	line=$(printf '%q ' "$@")
	if [ -n "$kill" ]; then
		screen-window-kill "$screen" "$window"
	fi
	screen-run-lines "$screen" "$window" ". $ALLEMANDE_HOME/env.sh" "${line% }"
}

locked() {
	{
		flock -x -w $FLOCK_WAIT 200 || exit 1
		"$@"
	} 200>/var/lock/screen-run.lock
}

screen-new() {
	local screen=$1
	(
		sleep "$SCREEN_NEW_DELAY_1"
		if ! screen -S "$screen" -X detach; then
			sleep "$SCREEN_NEW_DELAY_2"
			screen -S "$screen" -X detach
		fi
	) &
       	# shellcheck disable=SC2086
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

screen-window-new() {
	local screen=$1 window=$2
	if ! screen-exists "$screen"; then
		screen-new "$screen"
		screen -S "$screen" -X title "$window"
	else
		screen -S "$screen" -X screen -t "$window"
		screen -S "$screen" -X other
	fi
}

# this is not used by the main script
screen-window-select() {
	local screen=$1 window=$2
	screen -S "$screen" -X select "$window"
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

screen-stuff-line() {
	local screen=$1 window=$2
	shift 2
	local keys=$*
	screen-stuff "$screen" "$window" "$*^M"
}

screen-run-lines() {
	local screen=$1 window=$2
	shift 2
	locked screen-window-new "$screen" "$window"
	for line; do
		screen-stuff-line "$screen" "$window" "$line"
	done
}

# this is not used by the main script
screen-clear-scrollback() {
	local screen=$1 window=$2
	screen -S "$screen" -p "$window" -X eval "clear" "scrollback 0" "scrollback 15000"
}

screen-attach() {
	local screen=$1 window=${2:-}
	if [ -n "$window" ]; then
		screen -x "$screen" -p "$window"
	else
		screen -x "$screen"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	screen-run "$@"
fi

# version: 0.1.1
