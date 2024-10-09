#!/bin/bash
# [prompt]
# Explain like I'm five.

eli5() {
	local verbose= v=1	# use 'process' not 'proc', to be verbose
	local model= m=	# model
	local prompt= p=	# extra prompt

	eval "$(ally)"

	prompt="$prompt $*"

	local proc="proc"
	if [ "$verbose" = 1 ]; then
		proc="process"
	fi

	local prompt="What is this? Please ELI5 every detail, especially the parts that are not very obvious. Don't omit to explain anything even if it's 'advanced' or whatever. I'm not really five, after all. $prompt"

	$proc -m="$model" --empty-ok "$prompt"
}

if [ "$0" = "$BASH_SOURCE" ]; then
	eli5 "$@"
fi
