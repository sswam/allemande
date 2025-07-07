#!/usr/bin/env bash
# [prompt [reference files ...]]
# Query an LLM with the given prompt

query() {
	local model= m=	  # LLM model to use
	local system= s=  # system prompt

	eval "$(ally)"

	local prompt="${1:-}"
	shift || true

	local refs=("$@")

	local opts=()

	if [ -n "$system" ]; then
		opts+=("--system=$system")
	fi

	cat-named -p -S $'\n' --suppress-headings input "${refs[@]}" |
		llm process -m "$model" "${opts[@]}" --empty-ok "$prompt" | text-strip
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	query "$@"
fi

# version: 0.1.3
