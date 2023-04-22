#!/bin/bash -eua

progdir="$(dirname "$(readlink -f "$0")")"
cd "$progdir"

. ./env-work.sh

nt bb-voice

# xterm -e "bash -i -c 'nt core; core.sh; exec bash'" &
xterm -e "bash -i -c 'bbv-1-brain.sh; exec bash'" &
xterm -e "bash -i -c 'bbv-2-mike.sh; exec bash'" &
xterm -e "bash -i -c 'bbv-3-speak.sh; exec bash'" &

xterm -e "vi '$file'; exec bash" &
# code "$file" &
