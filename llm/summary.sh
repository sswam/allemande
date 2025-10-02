#!/bin/bash

# [prompt ...]
# Summarizes text using an AI model
#
# This script takes a prompt as input and summarises the input from stdin using an AI model.
# It uses the llm command-line tool to process the input and produce a concise summary to stdout.

summary() {
	local model= m=s  # default model: small
	local prompt= p=  # Extra prompt

	eval "$(ally)"

	# Construct the prompt
	prompt="Please summarize. Only give the summary. $prompt"

	# Process the input using llm
	process -m="$model" "$prompt" "$@"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	summary "$@"
fi

# Version: 1.0.6
