#!/usr/bin/env bash

# [spec name] [prompt]
# Create a spec from a user prompt

spec() {
	local model= m=	# LLM model
	local sample= s=1	# refer to hello.<ext> for style (e.g. hello.md)
	local sections= S=(summary features requirements)	# Sections to include
	local sections_file= F=$ALLEMANDE_HOME/llm/spec-sections.md	# Refer to sections file, or blank for none; trumps --sections
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
		confirm -t continue?
		;;
	*)
		echo >&2 "Warning, unusual format: $format"
		confirm -t continue?
		;;
	esac

	# style reference and prompt for -s option
	style="hello-$ext"
	if [ "$sample" = 1 -a -n "$(which-file "$style")" ]; then
		refs+=("$style")
		prompt="In the style of \`$style\`, $prompt"
	fi

	prompt="Please write a specfication \`$base\`, $prompt."

	# add prompting for sections, if any
	if [ -n "$sections_file" ]; then
		sections_file_basename=$(basename "$sections_file")
		prompt="$prompt Include sections as per $sections_file_basename."
		refs+=("$sections_file")
	elif [ "${#sections[@]}" -gt 0 ]; then
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
