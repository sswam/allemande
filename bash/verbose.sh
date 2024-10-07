#!/bin/bash
# v: echo and execute a command

exec=

echo_command() {
	if [ "$#" -eq 0 ]; then
		return 0
	fi
	out=`
		printf "%s" "${V_PS1:-}"
		printf "%q " "$@"
	`
	printf "%s\n" "${out% }" >&2
}

verbose() {
	echo_command "$@"
	$exec "$@"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	exec=exec
	v "$@"
fi
