#!/bin/bash -eu
# [arg ...]
echo "$*" > ~/.config/i3status/custom_message

pkill -SIGUSR1 py3status || true
