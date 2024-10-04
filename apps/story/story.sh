#!/bin/bash
# [options] < input > output
# Write a story

format= f=md	# format
illustrated= i=	# illustrated

eval "$(ally)"

prompt="$*"

prompt2="please write a story"

if [ "$prompt" ]; then
	prompt2="$prompt2, $prompt"
fi

if [ "$format" ]; then
	prompt2="$prompt2, in $format format"
fi

if [ "$illustrated" ]; then
	img='<img src="image_url" alt="ALT text" title="Title" width="1200" height="800">'
	case "$format" in
	md|txt)	img='![ALT text](image_url "Title"){width=1200 height=800}' ;;
	*)	echo >&2 "Unsupported format: $format, defaulting to HTML-style images" ;;
	esac
	prompt2="$prompt2, please add illustrations using \`$img\` tags
with good filenames in the same directory, and very descriptive ALT text which
we will use as an AI image generation prompt. The TITLE text can be a more
concise description. Consider suitable image dimensions."
fi

v process "$prompt2"
