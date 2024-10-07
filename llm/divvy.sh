#!/usr/bin/env bash

# [output files...]
# Separates stdin into several files (args)

divvy() {
	local prompt= p=	# Extra prompt
	local model= m=	# LLM model
	local number= n=	# Number of files, may be a number or descriptive text
	local ext= x=	# file extension for output files
	local prefix= P=	# prefix for output files

	eval "$(ally)"

	if [ "$ext" ]; then
		ext=".$ext"
	fi

	# arguments, the output files
	local output_files=("$@")

	# Check if at least one output file is specified
	# If not, the AI can choose the output file names.
	# We will be careful not to clobber in any case.
	if [ $# -gt 0 ]; then
		output_prompt="output files: ${output_files[*]}"
	else
		output_prompt="$number $ext output files"
		if [ "$prefix" ]; then
			output_prompt="$output_prompt with prefix \`$prefix\`"
		fi
		output_prompt="$output_prompt, e.g. \`${prefix}1$ext\` or \`${prefix}foo$ext\`"
	fi

	local prompt="Please divide, separate or classify the input into $output_prompt. $prompt
Output must be in the format:
#File: ${prefix}<name>$ext
content
#File: ${prefix}<secondname>$ext
content
..."

	process -m="$model" "$prompt" |
	split-files - | tee /dev/stderr |
	grep '^> ' | cut -c3- |
	xa cx-shebang
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	divvy "$@"
fi
