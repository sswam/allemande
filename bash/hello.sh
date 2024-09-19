#!/bin/bash -eu
# [name]
# Says Hello, world

# Notes:
# 	The `. opts` call gets options and prints usage automatically. No need to do that in the script.
# 	The header above is 1. arguments without program name, 2. short description of the program.
# 	This header format should be followed exactly, for `. opts` to print usage.
# 	These scripts can be used as a CLI tool or as a bash library thanks to the BASH_SOURCE stuff.
#	Please indent using tabs, and if commenting after a line of code, use a single tab for spacing.
#	Do not assume weird tool names are typos. I use many custom tools, including:
#	- `wich`, a better `which` that also finds non-execuable shell libs
#	When writing other scripts based on this one, please do NOT include these notes!

hello() {
	local l=en	# language [fr|de|jp|cn], defaults to English
	local s=()	# array of items for shopping
	local a=	# greet using AI
	local m=	# LLM model

	. opts

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
}

if [ "$BASH_SOURCE" = "$0" ]; then
	hello "$@"
fi
