#!/bin/bash

# [prompt ...]
# Summarizes text using an AI model

summary() {
	local m="s"	# default model

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	p="$*"

	# Construct the prompt
	p="Please summarize. $p. Only give the summary."

	# Process the input using llm
	llm process -m "$m" "$p"

	# restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	summary "$@"
fi

# Version: 1.0.4
