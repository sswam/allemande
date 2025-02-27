#!/usr/bin/env bash

# [url]
# Fetches and summarizes web content

process_content() {
	local url=$1
	local model=$2
	local prompt=$3

	web-text "$url" |
		proc -m="$model" "Please give a summary without any prelude, but with a heading reflecting the document. $prompt"
}

web_summary() {
	local name= n=                     # name of the output file
	local dir= d="$ALLEMANDE_HOME/gen" # directory to save the output
	local model= m=s                   # model for the summary
	local prompt= p=                   # extra prompt
	local save= s=1                    # save to output directory

	eval "$(ally)"

	# non-option arguments
	local url=${1:-}
	[ -n "$url" ] || usage "URL is required"

	# Check if we should save the output
	if [ "$save" = 1 ]; then
		# Check if output directory exists and is writable
		if [ ! -d "$dir" ]; then
			echo >&2 "Error: Output directory does not exist: $dir"
			save=0
		elif [ ! -w "$dir" ]; then
			echo >&2 "Error: Output directory is not writable: $dir"
			save=0
		fi
	fi

	# Get the name of the resource
	if [ -z "$name" ]; then
		name=$(que -m="$model" "What's a short filename to document this resource, lower-case with .md extension: $url")
	fi

	# Process the content
	if [ "$save" = 0 ]; then
		process_content "$url" "$model" "$prompt" "$name"
	else
		process_content "$url" "$model" "$prompt" "$name" | verbose tee -a "$dir/$name"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	web_summary "$@"
fi
