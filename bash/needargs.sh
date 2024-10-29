#!/usr/bin/env bash

# n prog args
# Verify required number of arguments are present, at least n
# Does not fail if there are insufficient args.
#
# This is useful to wrap tools that require an argument and do not work
# consistently as they should with 0 args, such as cat or file.
#
# It should be used to fix these broken tools, not for error checking.

needargs() {
	. unset-option-vars
	OPTS_ALLOW_UNKNOWN=1 eval "$(ally)"  # TODO this is error prone as opts already in the environment won't be passed through

	if [ "$#" -lt 2 ]; then
		die "n prog args required"
	fi

	local n="$1"
	local prog="$2"
	shift 2

	if [ "$#" -lt "$n" ]; then
		exit 0
	fi

	exec "$prog" "${OPTS_UNKNOWN[@]}" "$@"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	needargs "$@"
fi

# version: 0.1.0
