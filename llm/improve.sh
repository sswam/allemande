#!/bin/bash

# [file] "instructions to improve it" [reference files ...]
# Improve something using AI
set -e -u -o pipefail

improve() {
	local m=    # model
	local s=0   # refer to hello.<ext> for style
	local E=0   # do not edit
	local c=0   # concise
	local b=0   # use basenames

	. opts

	local file=$1
	local prompt=$2
	shift 2 || true
	local refs=("$@")

	if [ "$b" = 1 ]; then
		opt_b=("-b")
	else
		opt_b=()
	fi

	# Check if the file exists
	if [ ! -e "$file" ]; then
		local prog2=$(wich "$file")
		if [ ! -e "$prog2" ]; then
			echo >&2 "not found: $file"
			exit 1
		fi
		file=$prog2
	fi

	# resolve symlinks
	file=$(readlink -f "$file")

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

	prompt="Please improve \`$base\`, and bump the patch version if present, $prompt"

	if [ "$c" = 1 ]; then
		prompt="$prompt, Please reply concisely with only the changes."
	fi

	local input=$(cat_named.py -p "${opt_b[@]}" "$file" "${refs[@]}")

	# Backup original file
	if [ -e "$file~" ]; then
		move-rubbish "$file~"
	fi
	echo n | cp -i -a "$file" "$file~"   # WTF, there's no proper no-clobber option?!

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
	fi > "$file~"

	# check not empty
	if [ ! -s "$file~" ]; then
		echo >&2 "empty output"
		rm "$file~"
		exit 1
	fi

	# Compare original and improved versions
	if [ "$E" = 0 ]; then
		vimdiff "$file~" "$file"
	fi

	# Use swapfiles with -c option to preserve hardlinks
	swapfiles -c "$file" "$file~"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	improve "$@"
fi
