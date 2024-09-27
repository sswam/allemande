#!/bin/bash -eu
#
# What are you working on?

i=1800	# interval
t=300	# input timeout
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
		i3_popup_xterm -w -T="What are you working on?" note -t=waywo --timeout="$t" -L -1
		i3_update_message.sh $(note -t=waywo -n -A)
		sleep "$i" || true
	done
fi
