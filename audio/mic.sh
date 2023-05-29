#!/bin/bash -eu
# toggle-mic: Toggle microphone state

on=
off=

. opts

# suggested i3 config:
# bindsym $mod+m exec --no-startup-id toggle-mic.sh

TIMEOUT_MS=1000

# Check if we should turn the microphone on or off

if [ "$on" = 1 ]; then
	mic_state=off
elif [ "$off" = 1 ]; then
	mic_state=on
else
	# Get current microphone state
	mic_state=$(amixer get Capture | grep '\[on\]' > /dev/null && echo "on" || echo "off")
fi

# Toggle microphone state, or follow -on and -off options

if [ "$mic_state" == "on" ]; then
	amixer set Capture nocap
	notify-send -u normal -t $TIMEOUT_MS "Microphone" "Microphone is now muted."
else
	amixer set Capture cap
	notify-send -u normal -t $TIMEOUT_MS "Microphone" "Microphone is now unmuted."
fi
