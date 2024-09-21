#!/bin/bash

# [-m model] [prompt ...]
# Summarizes text using an AI model

summary() {
	local m="4m"  # Default model
	local prompt=""

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	# Construct the prompt
	if [ $# -gt 0 ]; then
		prompt="Please summarize, $*"
	else
		prompt="Please summarize"
	fi

	# Process the input using llm
	llm process -m "$m" "$prompt. Only give the summary."

	# restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	summary "$@"
fi

# Version: 1.0.4
