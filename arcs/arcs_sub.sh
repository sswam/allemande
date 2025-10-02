#!/bin/bash -eu
# [root folders]
# sync submodules with arcs

arcs-sub() {
	local verbose= v=   # show output even on success
	local no_net= N=    # don't sync on the network

	eval "$(ally)"

	local args=("$@")
	local arcs_opts=()
	
	if [ "$no_net" = 1 ]; then
		arcs_opts+=("-N")
	fi

	local status=0
	while IFS= read -r git; do
		if [ ! -d "$git" ]; then
			echo >&2 "Not a directory: $git"
			continue
		fi
		repo=$(dirname "$git")
		if [ "$verbose" = 1 ]; then
			verbose arcs "${arcs_opts[@]}" "$repo" || status=1
		else
			quiet-on-success arcs "${arcs_opts[@]}" "$repo" || status=1
		fi
	done < <(
		# process deeper repos first
		find "${args[@]}" -name '.git' |
		order |
		awk -F/ '{print NF-1, $0}' |
		order 1rn |
		cut -d' ' -f2-
	)
	return "$status"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	arcs-sub "$@"
fi

# version: 0.1.3
