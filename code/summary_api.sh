#!/bin/bash -eu

# [arg ...]
# Summarizes an API compactly in markdown with expert-level details

summary_api() {
	local model= m=  # LLM model

	. opts

	# Support long and short options
	model=${model:-$m}

	summary.sh -m="$model" "Please summarize the API compactly in markdown but including every detail an expert programmer would need to program for it. e.g. prototypes and very short descriptions. ${*:-}"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	summary_api "$@"
fi

# version: 0.1.1
