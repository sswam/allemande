#!/bin/bash

# [filename or extension]
# Echo the resulting prefix comment style for the given filename or extension

comment_style() {
	local show_block= b=  # show block comments

	eval "$(ally)"

	# Check if a filename is provided
	if [ $# -eq 0 ]; then
		usage 1
	fi

	filename="$1"

	# Extract extension if a filename is given
	local ext=${filename##*.}
	[[ "$filename" == "$ext" ]] && ext=$filename

	local comment_char="#"
	local block_start=""
	local block_end=""

	case "${ext,,}" in
	py)
		comment_char="#"
		block_start='"""'
		block_end='"""'
		;;
	c|h|cpp|hpp|h|cc|cxx|c++|hxx|ii|java|js|ts|php|cs|go|rs|swift|kt|scala|groovy|dart|v|d)
		comment_char="//"
		block_start="/*"
		block_end="*/"
		;;
	fs|nim|zig|vala|cr|wren|odin|jai|pony|haxe)
		comment_char="//"
		block_start=""
		block_end=""
		;;
	sh|py|pl|rb|lua|tcl|awk|sed|bash|zsh|fish|ps1|psm1|psd1|r|jl|crystal|elixir|ex|exs|ml|mli|coffee|haskell|hs|nim)
		comment_char="#"
		block_start=""
		block_end=""
		;;
	md)
# 		comment_char="[//]: #"
		comment_char=""
		block_start="<!--"
		block_end="-->"
		;;
	html|xml)
		comment_char=""
		block_start="<!--"
		block_end="-->"
		;;
	txt|json|yaml|yml|toml|ini|conf|cfg|properties|env|csv|tsv|rec|log|sql)
		comment_char=""
		block_start=""
		block_end=""
		;;
	lisp|clj|scm|rkt)
		comment_char=";"
		block_start=""
		block_end=""
		;;
	f|f90|f95|f03|f08)
		comment_char="!"
		block_start=""
		block_end=""
		;;
	vim)
		comment_char='"'
		block_start=""
		block_end=""
		;;
	*)
		comment_char=""
		block_start=""
		block_end=""
		;;
	esac

	# Output results
	printf "%s\n" "$comment_char"
	if [[ "$show_block" == 1 ]]; then
		printf "%s\n" "$block_start"
		printf "%s\n" "$block_end"
	fi

	# restore caller options
	eval "$old_opts"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	comment_style "$@"
fi

# version: 0.1.2
