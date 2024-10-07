#!/bin/bash

# [input] [file]
# Make input simpler

simple() {
	local model= m=   # LLM model

	eval "$(ally)"

	model=${model:-$m}

	prompt="Please make it simpler, in a good way. Keep anything you don't understand. $*"

	process -m="$model" "$prompt"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	simple "$@"
fi
