#!/bin/bash -eu
# toggle-mic: Toggle microphone state

# suggested i3 config:
# bindsym $mod+m exec --no-startup-id toggle-mic.sh

# Get current microphone state
mic_state=$(amixer get Capture | grep '\[on\]' > /dev/null && echo "on" || echo "off")

if [ "$mic_state" == "on" ]; then
    amixer set Capture nocap
    notify-send -u normal "Microphone" "Microphone is now muted."
else
    amixer set Capture cap
    notify-send -u normal "Microphone" "Microphone is now unmuted."
fi
