#!/bin/bash

# [prompt ...]
# Summarizes text using an AI model
#
# This script takes a prompt as input and generates a summary using an AI model.
# It uses the llm command-line tool to process the input and produce a concise summary.

summary() {
	local model= m=s	# default model: small

	eval "$(ally)"

	local prompt="$*"

	# Construct the prompt
	prompt="Please summarize. $prompt. Only give the summary."

	# Process the input using llm
	llm process -m "$model" "$prompt"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	summary "$@"
fi

# Version: 1.0.5
