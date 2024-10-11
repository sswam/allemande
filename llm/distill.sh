#!/bin/bash

# [prompt ...]
# Distills input down to its essentials

distill() {
	local model= m=	# LLM model [s|m|l], defaults to small
	local prompt= p=	# Optional user prompt

	eval "$(ally)"

	# Construct the prompt
	prompt="Please distill this down to its essentials. $* $prompt"

	# Process the input using llm
	process -m="$model" "$prompt"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	distill "$@"
fi

# Version: 1.0.0
