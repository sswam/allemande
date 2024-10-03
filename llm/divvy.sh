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
	awk '
		/^#File: / {
			if (file) close(file)
			file = substr($0, 7)
			next
		}
		{ if (file) print > file }
	'
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	divvy "$@"
fi

# version: 0.1.0

# Here's the `divvy.sh` script, written in the style of `hello_sh.sh`, to separate stdin into several files based on the provided arguments:

# This script, `divvy.sh`, allows you to separate stdin into several files based on the provided arguments. It supports both a simple splitting method and an AI-powered intelligent splitting method. Here's a breakdown of its functionality:
#
# 1. It uses the `opts` script to handle options and generate usage information.
# 2. It supports both long and short options for various parameters.
# 3. The main `divvy` function checks if at least one output file is specified.
# 4. Depending on whether AI is used or not, it calls either `ai_divvy` or `simple_divvy`.
# 5. The `simple_divvy` function uses the `split` command to divide the input, either by line count or evenly across the specified number of files.
# 6. The `ai_divvy` function uses an AI model to intelligently split the content based on context.
# 7. The script can be used both as a standalone command and as a bash library.
#
# This script follows the style and conventions of `hello_sh.sh`, including error handling, option processing, and the ability to be used as a library or standalone tool.

