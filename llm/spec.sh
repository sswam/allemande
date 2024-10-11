#!/usr/bin/env bash

# [spec name] [prompt]
# Create a spec from a user prompt

spec() {
	local model= m=	# LLM model
	local sample= s=1	# refer to hello.<ext> for style (e.g. hello.md)
	local sections= S=(summary features requirements)	# Sections to include
	local format= f=	# Output format [md|txt|html|json]
	local edit= e=1	# do not edit

	eval "$(ally)"

	local file=$1
	local prompt=${2:-}
	shift 2 || shift 1
	local refs=("$@")

	local dir=$(dirname "$file")
	local base=$(basename "$file")
	local ext=${base##*.}

	# if format is not given, use the file extension, or md by default
	if [ -z "$format" ]; then
		format="$ext"
	fi
	if [ -z "$format" ]; then
		format="md"
	fi

	# Check format
	case "$format" in
	md) ;;
	txt|html|json)
		echo >&2 "Warning, we recommend to use markdown format, not: $format"
		confirm continue?
		;;
	*)
		echo >&2 "Warning, unusual format: $format"
		confirm continue?
		;;
	esac

	# style reference and prompt for -s option
	style="hello-$ext"
	if [ "$s" = 1 -a -n "$(which-file "$style")" ]; then
		refs+=("$style")
		prompt="In the style of \`$style\`, $prompt"
	fi

	prompt="Please write a specfication \`$base\`, $prompt."

	# add prompting for sections, if any
	if [ "${#sections[@]}" -gt 0 ]; then
		prompt="$prompt Include sections for ${sections[*]}."
	fi

	local input=$(cat-named -p -b "${refs[@]}")

	if [ -z "$input" ]; then
		input=":)"
	fi

	# Create parent directory
	mkdir -p "$dir"

	# Generate spec
	printf "%s\n" -- "$input" | process -m="$model" "$prompt" |
	tee -a "$file"

	# edit the spec
	if (( "$edit" )); then
		$EDITOR "$file"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	spec "$@"
fi

# version: 0.1.1
