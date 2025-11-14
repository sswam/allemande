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
	local name= n=										 # name of the output file
	local dir= d="$ALLEMANDE_HOME/gen" # directory to save the output
	local model= m=s									 # model for the summary
	local prompt= p=									 # extra prompt
	local save= s=1										# save to output directory
	local name_method= M=slug					# method to generate name: slug, leaf, ai
	local regenerate= r=0							# regenerate if cached summary exists

	eval "$(ally)"

	# non-option arguments
	local url=${1:-}
	if [ -z "$url" ]; then
		usage "URL is required"
	fi

	# Check if we should save the output
	if [ "$save" = 1 ]; then
		# Check if output directory exists and is writable
		if [ ! -d "$dir" ]; then
			echo >&2 "Output directory does not exist: $dir"
			save=0
		elif [ ! -w "$dir" ]; then
			echo >&2 "Output directory is not writable: $dir"
			save=0
		fi
	fi

	if [ -n "$name" ]; then
		name_method="given"
	fi

	# Get the name of the resource
	case "$name_method" in
	given)
		# Name was already provided via -n flag, nothing to do
		:
		;;
	slug)
		# Use full URL without scheme, sanitized through slug tool later
		name="${url#*://}"
		;;
	leaf)
		# Use URL leaf name stem directly
		name="${url##*/}"
		# Remove query string and fragment
		name="${name%%\?*}"
		name="${name%%\#*}"
		;;
	ai)
		# Use AI to generate a canonical name based on URL
		# Emphasize short, sensible naming - likely page title from URL or shortest description
		name=$(que -m="$model" "Generate a short, canonical filename for this resource. Use the likely page title inferred from the URL, or the shortest way to describe what the page is about.")
		;;
	*)
		echo >&2 "Unknown name method: $name_method"
		exit 1
		;;
	esac

	# Lower case the name
	name="${name,,}"

	# Remove extension if present
	name="${name%.*}"

	# Run through slug tool
	name=$(slug "$name")

	# Add .md
	name="${name}.md"

	# Check if cached summary exists
	local output_file="$dir/$name"
	if [ "$save" = 1 ] && [ "$regenerate" = 0 ] && [ -f "$output_file" ]; then
		verbose cat "$output_file"
		return 0
	fi

	# Process the content
	if [ "$save" = 0 ]; then
		process_content "$url" "$model" "$prompt"
	else
		process_content "$url" "$model" "$prompt" | verbose tee "$output_file"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	web_summary "$@"
fi
