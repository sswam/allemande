#!/bin/bash
# confirm: ask a yes/no question, and optionally execute a command
# Usage: confirm [-y] [-n] [-o] [command]

#   -y  default to yes
#   -n  default to no
#   -o  do not return failure if the user cancels

function confirm() {
	local default is_command yes yn

	OPTIND=1
	cancel=1
	while getopts "yno" opt; do
		case "$opt" in
		y) default=y ;;
		n) default=n ;;
		o) cancel=0 ;;
		esac
	done
	shift $((OPTIND-1))

	is_command=
	prompt="$*"
	if [[ $prompt != *\? ]]; then
		prompt="$prompt ?"
		is_command=1
	fi

	confirmed=
	while true; do
		read -n 1 -p "$prompt " yn
		echo
		case "${yn:-${default:-}}" in
		y*)
			confirmed=1
			break
			;;
		n*)
			break
			;;
		esac
		echo -n "! [yn] "
	done

	if [ -n "$confirmed" ]; then
		if [ -n "$is_command" ]; then "$@"; fi
	else
		return "$cancel"
	fi
}

if [ "$0" = "$BASH_SOURCE" ]; then
	confirm "$@"
fi
