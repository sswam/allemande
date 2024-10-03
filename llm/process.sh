#!/usr/bin/env bash

# [input]
# Process input text using an LLM, optionally preserving indentation

process() {
	local model= m=	# LLM model to use
	local indent= i=1	# fix indentation

	eval "$(ally)"

	if [ "$indent" ]; then
		process_main "$@"
	else
		local input indent
		input=$(cat)
		indent=$(printf "%s\n" "$input" | aligno --detect)
		printf "%s\n" "$input" | process_main "$@" | aligno --apply "$indent"
	fi
}

process_main() {
	llm process -m "$m" "${@:-""}" | rstrip
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	process "$@"
fi

# version: 0.1.2
