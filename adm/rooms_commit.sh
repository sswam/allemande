#!/bin/bash -eu
#
# commit rooms

find "$ALLEMANDE_ROOMS" -type d -name .git | tac | (
	status=0
	while read -r git; do
		repo=$(dirname "$git")
		(
			if cd "$repo" && quiet-on-success arcs; then
				:
			else
				status=1
			fi
		)
	done
	exit $status
)
