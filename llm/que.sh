#!/usr/bin/env bash

# [prompt [attachment...]]
# Query an LLM for a concise answer

que() {
	local model= m=    # LLM model to use
	local system= s=    # system prompt

	eval "$(ally)"

	local prompt="${1:-}"
	shift || true

	opts=()
	if [ -n "$system" ]; then
		opts+=("--system=$system")
	fi

	concise="Please reply as concise as possible, with no boilerplate or unnecessary explanation."

	query -m="$model" "${opts[@]}" "$prompt"$'\n'"$concise" "$@" | text-strip
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	que "$@"
fi

# version: 0.1.1
