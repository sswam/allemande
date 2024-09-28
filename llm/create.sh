#!/bin/bash
# [file] "instructions to create it" [reference files ...]
# Write something using AI

create() {
	local m=	# model
	local s=1	# refer to hello.<ext> for style
	local E=0	# do not edit

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	local file=$1
	local prompt=$2
	shift 2
	local refs=("$@")

	# Check if file already exists
	if [ -e "$file" ]; then
		echo >&2 "already exists: $file"
		exit 1
	fi

	local dir=$(dirname "$file")
	local base=$(basename "$file")

	local ext=${base##*.}
	if [ "$ext" == "$base" ]; then
		ext="sh"
	fi

	# style reference and prompt for -s option
	style="hello_$ext.$ext"
	if [ "$s" = 1 -a -n "$(wich "$style")" ]; then
		refs+=("$style")
		prompt="in the style of \`$style\`, $prompt"
	fi

	mkdir -p "$dir"

	prompt="Please write \`$base\`, $prompt"

	local input=$(cat_named.py -p -b "${refs[@]}")

	if [ -z "$input" ]; then
		input=":)"
	fi

	comment_char="#"
	case "$ext" in
	c|cpp|java|js|ts|php|cs|go|rs)
		comment_char="//"
		;;
	sh|py|pl|rb)
		comment_char="#"
		;;
	md|txt)
		comment_char=""
		;;
	esac

	# Process input and save result
	printf "%s\n" "$input" | process -m="$m" "$prompt" |
	if [ -n "$comment_char" ]; then
		markdown_code.py -c "$comment_char"
	else
		cat
	fi > "$file"

	if [ -n "$comment_char" ]; then
		chmod +x "$file"
	fi

	if [ "$E" = 0 ]; then
		$EDITOR "$file"
	fi

	# restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	create "$@"
fi
