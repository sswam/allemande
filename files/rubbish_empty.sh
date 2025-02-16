#!/usr/bin/env bash

# empty the rubbish bin
# Empties all .rubbish directories

rubbish-empty() {
	local verbose= v=  # verbose

	eval "$(ally)"

	local base
	for base in "$HOME" $(qe df | tail -n +2 | awk '{print $6}'); do
		local rubbish="$base/.rubbish"

		if [ ! -d "$rubbish" ]; then
			continue
		fi

		cd "$rubbish" || continue

		if [ "$verbose" = 1 ]; then
			printf >&2 "%s\n" "$rubbish"
		fi

		find . -mindepth 1 -maxdepth 1 -print0 | xargs --no-run-if-empty -0 rm -f -v -r --
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	rubbish-empty "$@"
fi

# version: 0.1.1
