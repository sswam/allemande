#!/bin/bash -eu
# speaker:	use amixer to get / set volume, mute, unmute and toggle mute

get() {
	amixer get Master |
	while read -r line; do
		if [[ $line == *"[on]"* ]]; then
			out=$line
			out=${out#*[}
			out=${out%]*]}
			out=${out%\%*}
			printf "%s\n" "$out"
			break
		fi
	done
}

set() {
	local v=$1
	amixer set Master "${v}%"
}

mute() {
	amixer set Master off
}

unmute() {
	amixer set Master on
}

toggle() {
	amixer set Master toggle
}

speaker() {
	local cmd=${1:-toggle}
	shift || true
	case "$cmd" in
	get|set|mute|unmute|toggle)
		"$cmd" "$@"
		;;
	*)
		echo "Usage: $0 get|set|mute|unmute|toggle [args...]" >&2
		exit 1
		;;
	esac
}

if [ "$0" = "$BASH_SOURCE" ]; then
	speaker "$@"
fi
