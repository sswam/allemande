#!/bin/bash
# [cmd [arg ...]]
# echo and execute a command

exec=

echo-command() {
	if [ "$#" -eq 0 ]; then
		return 0
	fi
	out=$(
		printf "%s" "${V_PS1:-}"
		printf "%q " "$@"
	)
	printf "%s\n" "${out% }" >&2
}

verbose() {
	echo-command "$@"
	$exec "$@"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	exec=exec
	verbose "$@"
fi
