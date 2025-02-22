#!/bin/bash -eu
#
# commit rooms

rooms-commit() {
	local verbose= v=      # show output even on success

	eval "$(ally)"

	local status=0
	while IFS= read -r git; do
		repo=$(dirname "$git")
		if [ "$verbose" = 1 ]; then
			verbose arcs "$repo" || status=1
		else
			quiet-on-success arcs "$repo" || status=1
		fi
	done < <(find "$ALLEMANDE_ROOMS" -type d -name .git | tac)
	return "$status"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	. /opt/allemande/env.sh
	rooms-commit "$@"
fi

# version: 0.1.1
