#!/bin/bash

# [input] [file]
# Make input clearer

make_clear() {
	local model= m=   # LLM model

	eval "$(ally)"

	model=${model:-$m}

	prompt=$*

	prompt="Please make it more clear. $prompt"

	process -m="$model" "$prompt"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	make_clear "$@"
fi
