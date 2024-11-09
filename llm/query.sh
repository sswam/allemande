#!/usr/bin/env bash

# [prompt]
# Query an LLM with the given prompt

query() {
	local model= m=	# LLM model to use

	eval "$(ally)"

	llm query -m "$model" "$@" | text-strip
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	query "$@"
fi

# version: 0.1.1
