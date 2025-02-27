#!/usr/bin/env bash
#
# [ofile] "instructions to create it" [reference files ...]
# Write something using AI

create() {
	local model= m=     # LLM model
	local style= s=1    # refer to hello-<ext> for style
	local guidance= g=1 # refer to lang/guidance.md for style
	local edit= e=1     # edit
	local use_ai= a=1   # use AI, can turn off for testing with -a=0
	local quiet= q=0    # use only the user prompt
	local think= t=1    # encourage thinking

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

	# guidance reference and prompt for -g --guidance option
	guidance_ref="guidance-$ext.md"
	if ((guidance)) && [ "$(which-file "$guidance_ref")" ]; then
		echo >&2 "Using guidance reference: $guidance_ref"
		refs+=("$guidance_ref")
		prompt="refer to \`$guidance_ref\`, $prompt"
	fi

	# style reference and prompt for -s option
	if [ -n "$ext" ]; then
		style_ref="$ALLEMANDE_HOME/$ext/hello_$ext.$ext"
		if ((style)) && [ -e "$style_ref" ]; then
			refs+=("$style_ref")
			prompt="in the style of \`$style_ref\`, $prompt"
		fi
	fi

	mkdir -p "$dir"

	if [ "$quiet" = 0 ]; then
		prompt="Please write \`$base\`, $prompt"
	fi

	if [ "$think" = 1 ]; then
		prompt="$prompt  If necessary, and only where necessary, please think before and during your response, using <think> containers. For simple things, or when you already know the answer, it won't be necessary to think, and it saves the user money if you don't! Don't think for too long unless it seems important, or the user asks you to. When thinking, focus on generating new insights rather than restating the obvious parts of the question."
	fi

	local input=$(v cat-named --suppress-headings input -p -b "${refs[@]}")

	if [ -z "$input" ]; then
		input=":)"
	fi

	local comment_char=$(comment-style "$ext")

	if ((!"$use_ai")); then
		function process() { nl; }
	fi

	# Process input and save result
	printf "%s\n" "$input" | process -m="$model" "$prompt" |
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
