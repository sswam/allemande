#!/usr/bin/env bash

# <folder>
# Fetch and summarize emails from an IMAP folder

# shellcheck disable=SC1091
. confirm

email-fetch-summarize() {
	model= m=     # LLM model

	eval "$(ally)"

	local folder=${1:-}
	if [ -z "$folder" ]; then
		die "folder path required"
	fi

	mkdir -p "$(dirname "$folder")"

	# Fetch emails and store raw content
	imap-fetch -r -f "$folder" | tee "$folder".txt

	# Clean and process emails
	for email in "$folder"/*; do
		<"$email" email-clean |
			remove-links
		printf "\n\n"
	done | tee "${folder}-text.txt"

	# Calculate token count
	printf >&2 "token count and cost:\n"
	llm count -I -m="$model" <"${folder}-text.txt"

	# Generate summary
	confirm summarize "$folder" "$model"
}

summarize() {
	local folder=$1
	local model=$2

	proc -m="$model" \
		"Please give an executive overview of these emails for me ($USER), combining info from several emails where appropriate." \
		<"${folder}-text.txt" |
		tee "$folder"-summary.txt
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	email-fetch-summarize "$@"
fi

# version: 0.1.1
