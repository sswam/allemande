#!/usr/bin/env bash

# [yes/no question] [command]
# Ask a yes/no question, and optionally execute a command

confirm() {
	local default= d=	# default answer [y|n]
	local optional= o=	# do not return failure if the user cancels
	local tty= t=		# force tty input

	eval "$(ally)"

	local prompt="$*"
	local is_command=
	if [[ $prompt != *\? ]]; then
		prompt="$prompt ?"
		is_command=1
	fi

	local confirmed=

	ask_them() {
		read -r -n 1 -p "$prompt " yn
		echo
	}

	while true; do
		if [ -n "$tty" ]; then
			ask_them < /dev/tty > /dev/tty 2>&1
		else
			ask_them
		fi
		case "${yn:-${default}}" in
		y*|Y*)
			confirmed=1
			break
			;;
		n*|N*)
			break
			;;
		'')
			if [ -n "$default" ]; then
				confirmed=${default,,}
				break
			fi
			;;
		*)
			echo -n "! [yn] "
			;;
		esac
	done

	if [ -n "$confirmed" ]; then
		if [ -n "$is_command" ]; then "$@"; fi
		return 0
	else
		return "${optional:-1}"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	confirm "$@"
fi
