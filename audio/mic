#!/bin/bash -eu
# mic:	Toggle microphone state

n=1	# notify
t=1000	# notify timeout
#commands="get set mute unmute toggle status"

. opts

notify=$n
notify_timeout=$t
default="toggle"	# default command

# suggested i3 config:
# bindsym $mod+m exec --no-startup-id mic


# Check if we should turn the microphone on or off

#if [ "$on" = 1 ]; then
#	mic_state=off
#elif [ "$off" = 1 ]; then
#	mic_state=on
#else
#	# Get current microphone state
#	mic_state=$(amixer get Capture | grep '\[on\]' > /dev/null && echo "on" || echo "off")
#fi
#
## Toggle microphone state, or follow -on and -off options
#
#if [ "$mic_state" == "on" ]; then
#	amixer set Capture nocap
#	notify-send -u normal -t $notify_timeout "Microphone" "Microphone is now muted."
#else
#	amixer set Capture cap
#	notify-send -u normal -t $notify_timeout "Microphone" "Microphone is now unmuted."
#fi

get() {
	amixer get Capture |
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
		notify-send -u normal -t $notify_timeout "Microphone" "Microphone is set to $out%."
	fi
}

set() {
	local v=$1
	amixer set Capture "${v}%"
	if [ "$notify" = 1 ]; then
		notify-send -u normal -t $notify_timeout "Microphone" "Microphone is now set to $v%."
	fi
}

mute() {
	amixer set Capture nocap
	status
}

unmute() {
	amixer set Capture cap
	status
}

toggle() {
	amixer set Capture toggle
	status
}

status() {
	mute_state=$(amixer get Capture | grep '\[on\]' > /dev/null && echo "on" || echo "off")
	printf "%s\n" "$mute_state"
	if [ "$notify" = 1 ]; then
		if [ "$mute_state" = "on" ]; then
			notify-send -u normal -t $notify_timeout "Microphone" "Microphone is now unmuted."
		else
			notify-send -u normal -t $notify_timeout "Microphone" "Microphone is now muted."
		fi
	fi
}

mic() {
	local cmd=${1:-$default}
	shift || true
#	commands_pipe=${commands// /|}
	case "$cmd" in
	get|set|mute|unmute|toggle|status)
		"$cmd" "$@"
		;;
	*)
		echo "Usage: $0 $commands_pipe [args...]" >&2
		exit 1
		;;
	esac
}

if [ "$0" = "$BASH_SOURCE" ]; then
	mic "$@"
fi
