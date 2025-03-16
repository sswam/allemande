#!/usr/bin/env bash

# [command ...]
# Run a command quietly, show output only on failure

quiet-on-success() {
	eval "$(ally)"

	# non-option arguments
	command=("$@")

	# Create a temporary file for output
	temp_file=$(mktemp)
	trap 'rm -f "$temp_file"' RETURN

	# Run the command and capture output
	ret=0
	if "${command[@]}" > "$temp_file" 2>&1; then
		# Command succeeded, don't show any output
		ret=0
	else
		# Command failed, show the output
		ret=$?
		cat "$temp_file"
	fi
	return $ret
}

alias qs=quiet-on-success

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	quiet-on-success "$@"
fi

# TODO it would be nice to captue both stdout and stderr, and preserve their interleaving or even timestamps
