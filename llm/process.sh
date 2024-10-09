#!/usr/bin/env bash

# [options] [prompt ...]
# Process input text using an LLM, optionally preserving indentation

process() {
	local model= m=	# LLM model to use
	local indent= i=1	# fix indentation
	local empty_ok=	e=	# empty input is okay

	eval "$(ally)"

	local prompt="$*"

	opts=""
	if [ "$empty_ok" = 1 ]; then
		opts="--empty-ok"
	fi

	if [ "$indent" ]; then
		process_main "$prompt"
	else
		local input indent
		input=$(cat)
		indent=$(printf "%s\n" "$input" | aligno --detect)
		printf "%s\n" "$input" | process_main "$prompt" | aligno --apply "$indent"
	fi
}

process_main() {
	local prompt="$1"
	llm process -m "$model" $opts "$prompt" | rstrip
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	process "$@"
fi

# version: 0.1.2
