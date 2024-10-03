#!/usr/bin/env bash
#
# [ofile] "instructions to create it" [reference files ...]
# Write something using AI

create() {
	local model= m=	# LLM model
	local style= s=1	# refer to hello.<ext> for style
	local edit= e=1	# edit

	eval "$(ally)"

	local ofile=${1:-}
	shift || true
	local refs=("$@")

	[ -n "$ofile" ] || usage "Output file name is required"

	# Check if output file already exists
	if [ -e "$ofile" ]; then
		die "Output file already exists: $ofile"
	fi

	local dir=$(dirname "$ofile")
	local base=$(basename "$ofile")

	local ext=${base##*.}
	if [ "$ext" == "$base" ]; then
		ext="sh"
	fi

	# style reference and prompt for -s option
	style_ref="hello_$ext.$ext"
	if (( "$style" )) && -a [ "$(wich "$style_ref")" ]; then
		refs+=("$style_ref")
		prompt="in the style of \`$style_ref\`, $prompt"
	fi

	mkdir -p "$dir"

	prompt="Please write \`$base\`, $prompt"

	local input=$(cat_named.py -p -b "${refs[@]}")

	if [ -z "$input" ]; then
		input=":)"
	fi

	local comment_char=$(comment-style "$ext")

	# Process input and save result
	printf "%s\n" -- "$input" | process -m="$model" "$prompt" |
	if [ -n "$comment_char" ]; then
		markdown_code.py -c "$comment_char"
	else
		cat
	fi > "$ofile"

	# make the file executable if it is code
	if [ -n "$comment_char" ] && [ "$ext" -ne "md" ]; then
		chmod +x "$ofile"
	fi

	# Edit the file if requested
	if (( "$edit" )); then
		$EDITOR "$ofile"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	create "$@"
fi
