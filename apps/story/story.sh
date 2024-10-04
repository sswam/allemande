#!/bin/bash
# [options] < input > output
# Write a story
#

prompt= p=	# prompt
format= f=md	# format
illustrated= i=	# illustrated

eval "$(ally)"

prompt2="please write a story"

if [ "$prompt" ]; then
	prompt2="$prompt2, $prompt"
fi

if [ "$format" ]; then
	prompt2="$prompt2, in $format format"
fi

if [ "$illustrated" ]; then
	prompt2="$prompt2, please add image elements for illustrations with good filenames in the same directory, and very descriptive ALT text which we will use as an AI image generation prompt"
fi

v process "$prompt2"
