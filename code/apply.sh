#!/usr/bin/env bash

# [files...]
# Apply changes to a list of files by prompting an AI

apply-sh() {
	local model= m=gf   # LLM model to use, default Gemini Flash
	local changes= c=   # changes file, or stdin
	local edit= e=1     # open an editor after the AI does it's work

	eval "$(ally)"

	if [ $# -eq 0 ]; then
		return 0
	fi

	if [ -n "$changes" ]; then
		basename=$(basename "$changes")
	else
		basename=input
	fi
	for file; do
		if [ -e "$file"~ ]; then
			move-rubbish "$file"~
		fi
	done
	cat-named -p "$changes" "$@" |
	process -m="$model" \
	"Please copy the input files $*, applying the changes from '$basename' carefully, and output the complete files in the same format with '#File: foo' headers (and no black line after the header). If a file is unchanged, no need to include it. Use consistent indentation." |
		split-files -
	modify text-strip : "$@"
	if ((edit)); then
		for file; do
			if [ -e "$file"~ ]; then
				vimdiff "$file" "$file"~
			fi
		done
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	apply-sh "$@"
fi

# version: 0.1.0
