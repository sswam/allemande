#!/usr/bin/env bash

# [no arguments]
# Watch for changes in the current directory and estimate age of new images

watch-changes() {
	eval "$(ally)"

	awatch -p . -a -r -x png |
		perl -pe 'BEGIN { $| = 1 } s/\t/\a/g;' |
		while IFS=$'\a' read -r P I S0 S1; do
			if [ "$I" = 1 ] && [ -n "$S1" ]; then
				printf "%s\n" "$P"
			fi
		done | tee /dev/stderr | ~/allemande/safety/age/age_estimate_civitai.py
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	watch-changes "$@"
fi

# version: 0.1.1
