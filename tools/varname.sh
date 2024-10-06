#!/bin/bash -eu

varname() {
	# returns a random variable name that is not in use
	local prefix="${1:-varname}"
	while true; do
		local name="$prefix$RANDOM"
		if ! declare -p "$name" &>/dev/null; then
			varname=$name
			return
		fi
	done
}
