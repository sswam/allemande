#!/usr/bin/env bash

# [prompt [reference files ...]]
# Query an LLM with the given prompt

query() {
	local model= m= # LLM model to use

	eval "$(ally)"

	local prompt="${1:-}"
	shift || true

	local refs=("$@")

	cat-named -p -b --suppress-headings input "${refs[@]}" |
		llm process -m "$model" --empty-ok "$prompt" | text-strip
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	query "$@"
fi

# version: 0.1.2
