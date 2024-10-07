#!/bin/bash

# [input] [file]
# Make input more general or process file

general() {
	local model= m=   # LLM model

	eval "$(ally)"

	model=${model:-$m}

	prompt=$*

	prompt="Please make it more general. $prompt"

	process -m="$model" "$prompt"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	general "$@"
fi
