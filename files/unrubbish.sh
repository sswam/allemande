#!/usr/bin/env bash

# [file]
# Move the last changed file from ~/.rubbish/ back to CWD

unrubbish() {
	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail
	trap 'eval "$old_opts"' RETURN

	if [ -z "${RUBBISH:-}" ]; then
		M=$(mount-point "${1:-}")
		if [ "$M" = "$(mount-point "$HOME")" -o "$M" = / ]; then
			RUBBISH="$HOME/.rubbish"
		else
			RUBBISH="$M/.rubbish"
		fi
	fi

	local last_file

	# Find the last changed file in the rubbish directory
	last_file=$( ( i "$RUBBISH/" ls -tc1 || true ) | head -n1)

	if [ -z "$last_file" ]; then
		echo >&2 "No files found in $RUBBISH"
		return 1
	fi

	# Extract the original filename by removing the timestamp suffix
	local original_name=$(printf "%s" "$last_file" | sed -E 's/_[0-9]{8}_[0-9]{15}\+[0-9]{4}_[A-Za-z]{3}_[0-9]+$//')

	# Move the file back to the current working directory
	v mv -i "$RUBBISH/$last_file" "$original_name"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	unrubbish "$@"
fi
