#!/usr/bin/env bash

# [ofile] [reference files ...] < input
# Convert something in the style of another file or author

alla() {
	local prompt= p=	# Extra prompt
	local model= m=	# LLM model
	local style= s=0	# also refer to hello_$ext.$ext for style
	local edit= e=1	# edit the output file

	eval "$(ally)"

	local ofile=${1:-}
	shift || true
	local refs=("$@")

	[ -n "$ofile" ] || usage "Output file name is required"

	# Check if output file already exists
	if [ -e "$ofile" ]; then
		die "Output file already exists: $ofile"
	fi

	# Determine file extension and comment character
	local ext=${ofile##*.}
	[ "$ext" = "$ofile" ] && ext="sh"

	local comment_char=$(comment-style "$ext")

	# Prepare file type style reference
	style_ref="hello_$ext.$ext"
	if (( "$style" )) && [ "$(wich "$style_ref")" ]; then
		refs+=("$style_ref")
	fi

	# Prepare the prompt for the AI
	local prompt2="Please write \`$ofile\` in the style of $prompt"
	if [ "${#refs[@]}" -gt 0 ]; then
		if [ -n "$prompt" ]; then
			prompt2+=" and"
		fi
	       	prompt2+=" the provided reference files."
	fi

	local input=$(cat_named.py -p -b - "${refs[@]}")
	[ -z "$input" ] && input=":)"

	printf "%s\n" -- "$input" | process -m="$model" "$prompt2" |
	if [ -n "$comment_char" ]; then
		markdown_code.py -c "$comment_char"
	else
		cat
	fi > "$ofile"

	# make the file executable if it is code
	if [ -n "$comment_char" ] && [ "$ext" != "md" ]; then
		chmod +x "$ofile"
	fi

	# Edit the file if requested
	if (( "$edit" )); then
		$EDITOR "$ofile"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	alla "$@"
fi

# version: 0.1.1
