#!/usr/bin/env bash
#
# [ofile] "instructions to create it" [reference files ...]
# Write something using AI

create() {
	local model= m=   # LLM model
	local style= s=1  # refer to hello-<ext> for style
	local edit= e=1   # edit
	local use_ai= a=1 # use AI, can turn off for testing with -a=0
	local quiet= q=0  # use only the user prompt

	eval "$(ally)"

	local ofile=${1:-}
	local prompt=${2:-}
	shift 2 || shift 1 || true
	local refs=("$@")

	[ -n "$ofile" ] || usage "Output file name is required"

	# Check if output file already exists
	if [ -s "$ofile" ]; then
		die "Output file already exists: $ofile"
	fi

	local dir=$(dirname "$ofile")
	local base=$(basename "$ofile")

	local ext=${base##*.}
	if [ "$ext" == "$base" ]; then
		ext=""
	fi

	# style reference and prompt for -s option
	if [ -n "$ext" ]; then
		style_ref="hello-$ext"
		if (("$style")) && [ "$(which-file "$style_ref")" ]; then
			refs+=("$style_ref")
			prompt="in the style of \`$style_ref\`, $prompt"
		fi
	fi

	mkdir -p "$dir"

	if [ "$quiet" = 0 ]; then
		prompt="Please write \`$base\`, $prompt"
	fi

	local input=$(v cat-named -p -b "${refs[@]}")

	if [ -z "$input" ]; then
		input=":)"
	fi

	local comment_char=$(comment-style "$ext")

	if ((!"$use_ai")); then
		function process() { nl; }
	fi

	# Process input and save result
	printf "%s\n" -- "$input" | process -m="$model" "$prompt" |
		if [ -n "$comment_char" ]; then
			markdown-code -c "$comment_char"
		else
			cat
		fi >"$ofile"

	# make the file executable if appropriate
	chmod-x-shebang "$ofile"

	# Edit the file if requested
	if (("$edit")); then
		$EDITOR "$ofile"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	create "$@"
fi
