#!/bin/bash -eu

# I'll update `speaker.sh` to add notifications and make it similar to `mic.sh`. Here's the edited version:

# speaker:	use amixer to get / set volume, mute, unmute and toggle mute

n=1	# notify
t=1000	# notify timeout

. opts

notify=$n
notify_timeout=$t
default="toggle"	# default command

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
	if [ "$notify" = 1 ]; then
		notify-send -u normal -t $notify_timeout "Speaker" "Volume is set to $out%."
	fi
}

set() {
	local v=$1
	amixer set Master "${v}%"
	if [ "$notify" = 1 ]; then
		notify-send -u normal -t $notify_timeout "Speaker" "Volume is now set to $v%."
	fi
}

mute() {
	amixer set Master off
	status
}

unmute() {
	amixer set Master on
	status
}

toggle() {
	amixer set Master toggle
	status
}

status() {
	mute_state=$(amixer get Master | grep '\[on\]' > /dev/null && echo "on" || echo "off")
	printf "%s\n" "$mute_state"
	if [ "$notify" = 1 ]; then
		if [ "$mute_state" = "on" ]; then
			notify-send -u normal -t $notify_timeout "Speaker" "Speaker is now unmuted."
		else
			notify-send -u normal -t $notify_timeout "Speaker" "Speaker is now muted."
		fi
	fi
}

speaker() {
	local cmd=${1:-$default}
	shift || true
	case "$cmd" in
	get|set|mute|unmute|toggle|status)
		"$cmd" "$@"
		;;
	*)
		echo "Usage: $0 get|set|mute|unmute|toggle|status [args...]" >&2
		exit 1
		;;
	esac
}

if [ "$0" = "${BASH_SOURCE[0]}" ]; then
	speaker "$@"
fi
