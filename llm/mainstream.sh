#!/bin/bash

# [input] [file]
# This script makes text more mainstream or accessible

mainstream() {
	local model= m=   # LLM model

	eval "$(ally)"

	model=${model:-$m}

	prompt="Please make this text more mainstream and accessible: $"

	process -m="$model" "$prompt"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	mainstream "$@"
fi
