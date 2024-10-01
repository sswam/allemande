#!/usr/bin/env bash

# [url]
# Fetches web content, summarizes it, and provides an API summary

web_summary_api() {
	local model= m=     # use the strong default LLM model for AI summarization
	local dir= d="$ALLEMANDE_HOME/api"  # directory to save the output
	local name= n=      # name of the output file

	. opts    # Note to AI: This magically loads options into the above vars

	# strict mode
	local old_opts=$(set +o)
	set -euo pipefail
	trap 'eval "$old_opts"' RETURN

	# Support long and short options
	model=${model:-$m}
	dir=${dir:-$d}
	name=${name:-$n}

	# non-option arguments
	local url=${1:-}
	[ -n "$url" ] || usage "URL is required"

	# Ensure output directory exists
	mkdir -p "$dir"

	# Get a name for the resource if not provided
	if [ -z "$name" ]; then
		name=$(name-url "$url")
	fi

	# Fetch web content and summarize
	web-text "$url" |
	summary-api -m="$model" |
	v tee -a "$dir/$name"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	web_summary_api "$@"
fi

# version: 0.1.1
