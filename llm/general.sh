#!/bin/bash

# [input] [file]
# Make input more general or process file

general() {
	local model= m=   # LLM model
	local prompt= p=  # custom prompt

	. opts    # Note to AI: This magically loads options into the above vars

	# Support long and short options
	model=${model:-$m}
	prompt=${prompt:-$p}

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail
	trap "eval $old_opts" RETURN

	# non-option arguments
	local input="$*"

	prompt="Please make it more general. $prompt"

	printf "%s\n" "$input" | process -m="$model" "$prompt"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	general "$@"
fi
