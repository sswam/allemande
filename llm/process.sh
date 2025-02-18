#!/usr/bin/env bash

# [prompt [reference files ...]]
# Process input text using an LLM, optionally preserving indentation

process() {
	local model= m=	# LLM model to use
	local indent= i=1	# fix indentation
	local empty_ok=	e=	# empty input is okay

	eval "$(ally)"

	local prompt="${1:-}"
	shift || true

	local refs=("$@")

	opts=""
	if [ "$empty_ok" = 1 ]; then
		opts="--empty-ok"
	fi

	cat-named -p -S $'\n' --suppress-headings input - "${refs[@]}" |
	if [ "$indent" ]; then
		local indent
		input=$(cat)
		indent=$(printf "%s\n" "$input" | aligno --detect)
		process_main "$prompt" <<< "$input" | aligno --apply "$indent" | text-strip
	else
		process_main "$prompt"
	fi
}

process_main() {
	local prompt="$1"
	llm process -m "$model" $opts "$prompt" | text-strip
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	process "$@"
fi

# version: 0.1.3
