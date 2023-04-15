#!/bin/bash -eu

set -a

progdir="$(dirname "$(readlink -f "$0")")"
cd "$progdir"

. ./env.sh

nt bb-voice

xterm -e "bash -i -c 'bbv-1-brain.sh; exec bash'" &
xterm -e "bash -i -c 'bbv-2-mike.sh; exec bash'" &
xterm -e "bash -i -c 'bbv-3-speak.sh; exec bash'" &

xterm -e "vi '$file'; exec bash" &
code "$file" &
