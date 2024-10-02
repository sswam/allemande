#!/bin/bash -e
# command [arg ...] : [file ...]
# run a command on each file in a list

each() {
	local command=()

	while [ "$1" != : ] && [ "$#" -gt 0 ]; do
		command+=("$1")
		shift
	done

	if [ "$1" != : ]; then
		echo >&2 "usage: `basename "$0"` command arg ... : file ..."
		exit 1
	fi

	shift

	fail=0
	local old_options=$(set +o)
	set +e

	for file in "$@"; do
		"${command[@]}" "$file"
		fail=$((fail + $?))
	done

	eval "$old_options"
	return $fail
}

if [ "$BASH_SOURCE" == "$0" ]; then
	each "$@"
fi
