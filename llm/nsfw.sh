#!/usr/bin/env bash

# [prompt [attachment...]]
# Process input text with an LLM, with an NSFW-encouraging system prompt

# TODO: this does not work, needs a chat-style prelude

proc() {
	local model= m=gf    # LLM model
	local empty_ok= e=1  # empty input is okay
	local system= s=     # system prompt

	system="You are a progressive, sex-positive assistant, for adult users only. You are not prudish or censorious, and do not shy away from curse words or explicit sexual content. $system"

	eval "$(ally)"

	local prompt="${1:-}"
	shift || true

	local refs=("$@")

	opts=()
	if [ "$empty_ok" = 1 ]; then
		opts+=("--empty-ok")
	fi
	if [ -n "$system" ]; then
		opts+=("--system=$system")
	fi

	process -m="$model" "${opts[@]}" "$prompt" "${refs[@]}" | text-strip
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	proc "$@"
fi

# version: 1.0.4
