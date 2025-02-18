#!/usr/bin/env bash

# [filename or extension]
# Saves stdin and optionally runs a program with the saved file

save() {
	local dest

	# If no arguments, save to 'saved' with incrementing suffix
	noclobber=0

	if [ $# -eq 0 ]; then
		ext=""
		dest=save
		noclobber=1
	elif [[ $1 == .* ]]; then
		# It's an extension
		ext="$1"
		dest="save$ext"
		noclobber=1
		shift
	else
		dest="$1"
		shift
	fi

	if ((noclobber)); then
		while [ -e "$dest" ]; do
			if [[ $dest =~ ^save\.([0-9]+)$ext$ ]]; then
				dest="save.$((${BASH_REMATCH[1]} + 1))$ext"
			else
				dest="save.1$ext"
			fi
		done
	fi

	# Save stdin to destination file
	cat >"$dest"

	# If program and args provided, run them with the saved file
	if [ $# -gt 0 ]; then
		"$@" "$dest"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	save "$@"
fi

# version: 0.1.1
