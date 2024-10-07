#!/bin/bash
# sleep-log - log the time remaining in a sleep

# I'm experimenting with sourceable functions, that we can also run directly.

sleep-log() {
	local notify=0
	local urgency

	OPTIND=1
	while getopts "nu:" opt; do
		case "$opt" in
		n)
			notify=1
			;;
		u)
			urgency="$OPTARG"
			;;
		esac
	done
	shift $((OPTIND-1))
	: ${urgency:=normal}
	local d=${1:-30} step=${2:-10}
	local hold_ms=${3:-$[$step * 1000 - 1]}

	if [ "$step" -gt "$d" ]; then
		step="$d"
	fi
	while [ "$d" -gt 0 ]; do
		echo -n "$d " >&2
		if [ "$notify" = 1 ]; then
			local desc=$(describe-interval "$d")
			notify-send -u "$urgency" -t "$hold_ms" "$desc"
		fi
		sleep "$step"
		d=$[d-step]
	done
	echo >&2
}

if [ "$0" = "$BASH_SOURCE" ]; then
	sleep-log "$@"
fi
