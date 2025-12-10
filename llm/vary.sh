#!/usr/bin/env bash
# [text to vary]
# Varies the provided text in different ways using AI

# shellcheck disable=SC1007,SC2034  # Disable certain shellcheck rules that conflict with ally options parser syntax

vary() {
	local model= m=s          # LLM model
	local num_variations= n=1 # number of variations to generate
	local prefix= p=          # optional prefix to add to the prompt

	eval "$(ally)" # Note to AI: This is our magickal options parser and more.

	local input_text="$*"
	if [ -z "$input_text" ]; then
		# Read from stdin if no arguments
		input_text=$(cat)
	fi

	if [ -z "$input_text" ]; then
		usage "Please provide text to vary, either as arguments or via stdin."
		exit 1
	fi

	local prompt="Please vary this text in different ways! Thanks for being awesome <3"
	if [ -n "$num_variations" ] && [ "$num_variations" -gt 0 ]; then
		prompt+=" Give $num_variations variation/s, just on separate lines/paragraphs, not numbered."
	fi
	if [ -n "$prefix" ]; then
		prompt+=" $prefix"
	fi
	prompt+=" Original text: $input_text"

	process -m="$model" "$prompt"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	vary "$@"
fi

# version: 0.1.0
