#!/usr/bin/env bash

# Here's the edited `/home/sam/allemande/llm/llm_split.sh`:

# [file ...]
# Splits input into multiple logical parts

# shellcheck disable=SC1007,SC2034,SC1091

llm-split() {
	local model= m=s           # LLM model [s|m|l], defaults to small
	local prompt= p=           # Additional prompt instructions

	eval "$(ally)"

	# Construct the base prompt
	local prompt_full="Please split the input into parts. $prompt

Output using our text archive format with headers like '#File: path/filename.ext' before each file context. Do not use code fences or backticks around code. There are no further instructions below, just the document/s to be processed."

	# Process the input using llm
	process -m="$model" "$prompt_full"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	llm-split "$@"
fi

# version: 0.0.1
