#!/bin/bash -eu

screen=${1:-allemande}

# This reads a list of window names and commands from stdin, tab separated.

# create a screen and detach
(sleep 0.1; screen -S "$screen" -X detach) &
screen -U -dRR "$screen"

IFS=$'\t'
read -r window command
screen -S "$screen" -X title "$window"
sst "$screen" "$window" "$command"

while read -r window command; do
	screen -S "$screen" -X screen -t "$window"
	sst "$screen" "$window" "$command"
done


#screen-ensure() {
#	local screen=$1
#	if ! screen-exists "$screen"; then
#		screen-new "$screen"
#	fi
#}
