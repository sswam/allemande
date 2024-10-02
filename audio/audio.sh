#!/bin/bash -eu

# Control the microphone and speaker
# Version: 1.0.4

audio_control() {
	local notify= n=1	# notify
	local notify_timeout= t=1000	# notify timeout in ms

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail
	trap 'eval "$old_opts"' RETURN

	notify=${notify:-$n}
	notify_timeout=${notify_timeout:-$t}

	local default="toggle"

	local device=${1:-}
	local cmd=${2:-$default}
	shift 2 || shift 1 || true

	case "$device" in
	mic)
		case "$cmd" in
		get|set|mute|unmute|toggle|status)
			"mic_$cmd" "$@"
			;;
		*)
			usage "Usage: $prog mic get|set|mute|unmute|toggle|status [args...]"
			;;
		esac
		;;
	speaker)
		case "$cmd" in
		get|set|mute|unmute|toggle|status)
			"speaker_$cmd" "$@"
			;;
		*)
			usage "Usage: $prog speaker get|set|mute|unmute|toggle|status [args...]"
			;;
		esac
		;;
	*)
		usage "Usage: $prog mic|speaker ..."
		;;
	esac
}

# TODO could make mic and speaker functions
# This idea of integrating the scripts is kind of bad, anyway.

mic_get() {
	local out
	out=$(amixer get Capture | grep '\[on\]' | sed -E 's/.*\[([0-9]+)%\].*/\1/')
	if [ -z "$out" ]; then
		return 1
	fi
	echo "$out"
	notify "Microphone" "Microphone is set to $out%."
}

mic_set() {
	if [ $# -eq 0 ]; then
		echo "Usage: mic_set <volume>"
		return 1
	fi
	amixer set Capture "$1%"
	notify "Microphone" "Microphone is now set to $1%."
}

mic_mute() {
	amixer set Capture nocap
	mic_status
}

mic_unmute() {
	amixer set Capture cap
	mic_status
}

mic_toggle() {
	amixer set Capture toggle
	mic_status
}

mic_status() {
	local mute_state
	if amixer get Capture | grep -q '\[on\]'; then
		mute_state="on"
	else
		mute_state="off"
	fi
	echo "$mute_state"
	notify "Microphone" "Microphone is now ${mute_state}."
}

speaker_get() {
	local out
	out=$(amixer get Master | grep '\[on\]' | sed -E 's/.*\[([0-9]+)%\].*/\1/')
	if [ -z "$out" ]; then
		return 1
	fi
	echo "$out"
	notify "Speaker" "Speaker is set to $out%."
}

speaker_set() {
	if [ $# -eq 0 ]; then
		echo "Usage: speaker_set <volume>"
		return 1
	fi
	amixer set Master "$1%"
	notify "Speaker" "Speaker is now set to $1%."
}

speaker_mute() {
	amixer set Master off
	notify "Speaker" "Speaker is now off."
}

speaker_unmute() {
	amixer set Master on
	notify "Speaker" "Speaker is now on."
}

speaker_toggle() {
	amixer set Master toggle
	speaker_status
}

speaker_status() {
	local state
	if amixer get Master | grep -q '\[on\]'; then
		state="on"
	else
		state="off"
	fi
	echo "$state"
	notify "Speaker" "Speaker is now $state."
}

notify() {
	if [ "$notify" = 1 ]; then
		notify-send -u normal -t "$notify_timeout" "$1" "$2"
	fi
}

if [ "$0" = "$BASH_SOURCE" ]; then
	prog=$(basename "$0")
	case "$prog" in
	mic|speaker)
		audio_control "$prog" "$@"
		;;
	*)
		audio_control "$@"
		;;
	esac
fi
