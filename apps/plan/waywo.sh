#!/bin/bash -eu
#
# What are you working on?

i=1800	# interval
t=300	# input timeout
T=60	# warn when timeout is running low
f=	# Run in the foreground
q=	# Quit any running waywo
e=	# Edit the waywo file

. opts

if [ -n "$e" ]; then
	note -e -t=waywo
elif [ -z "$f" ]; then
	v daemonize "$0" -f "${OPTS[@]}" "$@" &
elif [ -n "$q" ]; then
	echo "Got quit signal" >&2
else
	while true; do
		i3_popup_xterm -w -T="What are you working on?" note -t=waywo --timeout="$t" --warn-timeout="$T" -L -1
		i3_update_message.sh $(note -t=waywo -n -A)

		# try to sync with the clock
		second_of_the_day=$(( $(date +%s) - $(date -d "00:00" +%s) ))
		delay=$(( i - second_of_the_day % i ))
		if [ $delay -le $(( i / 2 )) ]; then
			delay=$(( delay + i ))
		fi
		sleep "$delay" || true
	done
fi
