#!/bin/bash
# [prog.py] "instructions to create it" [reference files ...]
# Write a program using AI

prog() {
	local m=	# model
	local s=1	# refer to hello.<ext> for code style
	local E=0	# do not edit

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	local prog=$1
	local prompt=$2
	shift 2
	local refs=("$@")

	# Check if program already exists
	if [ -e "$prog" ]; then
		echo >&2 "already exists: $prog"
		exit 1
	fi

	local dir=$(dirname "$prog")
	local base=$(basename "$prog")

	local ext=.${prog##*.}
	if [ "$ext" == ".$base" ]; then
		ext=".sh"
	fi

	# Code style reference and prompt for -s option
	if [ "$s" = 1 ]; then
		refs+=("hello$ext")
		prompt="in the style of \`hello$ext\`, $prompt"
	fi

	mkdir -p "$dir"

	prompt="Please write \`$base\`, $prompt"

	local input=$(cat_named.py -p -b "${refs[@]}")

	if [ -z "$input" ]; then
		input=":)"
	fi

	# Process input and save result
	printf "%s\n" "$input" | process -m="$m" "$prompt" | markdown_code.py -c '#' > "$prog"

	chmod +x "$prog"
	if [ "$E" = 0 ]; then
		$EDITOR "$prog"
	fi

	# restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	prog "$@"
fi
