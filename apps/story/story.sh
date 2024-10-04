#!/usr/bin/env bash

# [options] [filename.md|html [prompt]] < input
# Write me a story!

story() {
	local illustrated= i=	# illustrate, guidance
	local model= m=	# model
	local edit= e=1	# open in the editor before illustrating
	local view= v=1	# view the result in Chrome with markdown plugin

	eval "$(ally)"

	local filename="${1:-story.md}"
	shift || true
	local prompt="$*"

	local format="${filename##*.}"

	local prompt2="please write a story"

	if [ "$prompt" ]; then
		prompt2="$prompt2, $prompt"
	fi

	if [ "$format" ]; then
		prompt2="$prompt2, in $format format"
	fi

	if [ "$illustrated" ]; then
		local img='<img src="image_name.png" alt="ALT text" width="1200" height="800">'
		case "$format" in
		md | txt) img='![ALT text](imag_name.png){width=1200 height=800}' ;;
		*) echo >&2 "Unsupported format: $format, defaulting to HTML-style images" ;;
		esac
		prompt2="$prompt2, please add illustrations using \`$img\` tags
with good filenames (PNG) in the same directory, and very descriptive ALT text which
we will use as an AI image generation prompt. Choose a variety of suitable image dimensions as appropriate, aspect is important but we can adjust the scale. $illustrated"
	fi

	v llm process --model="$m" --empty-ok "$prompt2" | tee "$filename"

	if [ "$edit" ]; then
		${EDITOR:-vi} "$filename"
	fi

	if [ "$illustrated" ]; then
		illustrate.py --debug --prompt0 "${illustrated#1}" "$filename"
	fi

	if [ "$view" ]; then
		chrome "$filename"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	story "$@"
fi

# version: 0.1.1
