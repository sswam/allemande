#!/bin/bash

# [name]
# Says Hello, world

hello_sh() {
	local l=en	# language [fr|de|jp|cn], defaults to English
	local s=()	# array of items for shopping
	local a=	# greet using AI
	local m=	# LLM model

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	local who=${1:-}	# Set 'who' to the first argument
	local greeting="Hello"	# Default greeting in English

	# Set greeting based on selected language
	case "$l" in
		fr) greeting="Bonjour" ;;
		de) greeting="Hallo" ;;
		jp) greeting="こんにちは" ;;
		cn) greeting="你好" ;;
	esac

	# Generate greeting using AI or print simple greeting
	if [ "$a" = 1 ]; then
		query -m="$m" "Please greet ${who:-the world} in '$l' language. Be creative, but not more than 50 words.\n"
	else
		printf "%s, %s\n" "$greeting" "${who:-world}"
	fi

	# Print shopping list if items are provided
	if [ "${#s[@]}" -gt 0 ]; then
		echo
		echo "Shopping list:"
		for item in "${s[@]}"; do
			printf -- "- %s\n" "$item"
		done
	fi

	# restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	hello_sh "$@"
fi

# Important Notes for AI:

# AVOID DEEP INDENTATION OR NESTING, better to use if/elif or a function. This is the number one rule!
# Test negative cases first, and use continue, break, or return to avoid deep nesting.
#
# We use the `-e` `-u` and `-o pipefail` options, so be careful to avoid accidentally exiting:
# - Do not shorten if statements, for example not: `[ -n "$var" ] && do_something`
#
# The `. opts` call gets options and prints usage automatically. No need to do that in the script.
#
# The first lines 1. shebang, 2. arguments without program name, 3. short description of the program.
# This header format should be followed exactly, so that `. opts` can print usage.
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
# We assume the client script is using `-e`, so `return 1` should end up as `exit 1` normally.
#
# When writing other scripts based on this one, please do not include these notes!
