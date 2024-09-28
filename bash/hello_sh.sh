#!/bin/bash

# [user's name]
# Says Hello, world

hello_sh() {
	local language= l=en	# language [fr|de|jp|cn], defaults to English
	local shopping=() s=(milk)	# array of items for shopping
	local use_ai= a=	# greet using AI
	local model= m=	# LLM model

	. opts	# Note to AI: This magically loads options into the above vars

	# Note to AI: The following supports the short options above
	# TODO can we do this in the opts script?
	language=${language:-$l}
	shopping=("${shopping[@]}" "${s[@]}")
	use_ai=${use_ai:-$a}
	model=${model:-$m}

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	# non-option arguments
	local user_name=${1:-world}	# Set 'who' to the first argument

	# Set greeting based on selected language
	local greeting="Hello"	# Default greeting in English
	case "$language" in
	fr)
		greeting="Bonjour"
		;;
	de)
		greeting="Hallo"
		;;
	jp)
		greeting="こんにちは"
		;;
	cn)
		greeting="你好"
		;;
	en)
		;;
	*)
		echo >&2 "unknown language: $language"
		exit 1
		;;
	esac

	# Generate greeting using AI or print simple greeting
	if [ "$use_ai" = 1 ]; then
		query -m="$model" \
			"Please greet ${user_name:-the world} in $language."\
			"Be creative, but not more than 50 words."
	else
		printf "%s, %s\n" "$greeting" "$user_name"
	fi

	# Print shopping list if items are provided
	if [ "${#shopping[@]}" -gt 0 ]; then
		shopping_list --use-ai="$use_ai" --model="$model" "${shopping[@]}"
	fi

	# restore caller options
	eval "$old_opts"
}

shopping_list() {
	local use_ai= a=	# greet using AI
	local model= m=	# LLM model

	. opts

	# Support long and short options
	use_ai=${use_ai:-$a}
	model=${model:-$m}

	local shopping=("$@")

	echo
	echo "Shopping list:"
	for item in "${shopping[@]}"; do
		printf -- "- %s\n" "$item"
	done | 
	if [ "$use_ai" = 1 ]; then
		process -m="$model" \
			"Please echo the input and add any extra "\
			"items we might need, in $language."
	else
		cat
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	hello_sh "$@"
fi

# version: 0.1.0

# Important Notes for AI:

# Do not remove comments, logging or blank lines, especially not TODO, FIXME, XXX.
# Do not remove ANYTHING unnecessarily. If you are 1000% sure something is wrong,
# comment it out rather than removing it.
# 
# AVOID DEEP INDENTATION OR NESTING, better to use if/elif or a function. This is the number one rule!
# If needed, we can use variables to avoid repeating parts of conditions.
# Test negative cases first, and use continue, break, or return to avoid deep nesting.
#
# We use the `-e` `-u` and `-o pipefail` options, so be careful to avoid accidentally exiting:
# - Do not shorten if statements, for example not: `[ -n "$var" ] && do_something`
# Generally, if things go wrong, return 1 rather than continuing.
#
# The `. opts` call gets options and prints usage automatically. No need to do that in the script.
#
# The first lines 1. shebang, 2. arguments without program name, 3. short description of the program.
# This header format must be followed exactly, so that `. opts` can print usage.
#
# These scripts can be used as CLI tools or as a bash library thanks to the BASH_SOURCE stuff.
#
# If sensible and simple to do so, write tools that can process several files in one invocation.  # XXX not sure
# Zero is holy! It is not an error to pass zero files to process. Just naturally do nothing in that case.
#
# Do not assume weird tool names are typos. I use many custom tools, including:
# - `wich`, a better `which` that also finds non-execuable shell libs XXX maybe I should rename it
#
# Our functions might be used from other scripts, so on error return 1, do not exit 1.
# We assume the client script is using `-e`, so `return 1` normally becomes `exit 1`.
#
# Error and other commentary must be printed to stderr: echo >&2 "Error: something went wrong"
#
# When writing other scripts based on this one, please do not include these notes!
