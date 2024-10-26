#!/usr/bin/env bash

# [input files...]
# Compare two or more texts and highlight similarities and differences

diffy() {
	local output_format= f=unified # Output format [unified|side-by-side|context]
	local context_lines= c=3       # Number of context lines
	local ignore_case= i=          # Ignore case differences
	local ignore_whitespace= w=1   # Ignore whitespace differences
	local use_color= C=            # Use color output
	local model= m=                # LLM model for AI-enhanced diff
	local use_ai= a=1              # use AI or not?
	local economy= e=              # Economy mode, only show the AI the diff not the files
	local diff= d=                 # Use diff or not
	local prompt= p=               # Extra prompt for the AI

	eval "$(ally)"

	if [ "$#" -lt 2 ]; then
		usage "At least two input files are required"
	fi

	if [ "$economy" = 1 ]; then
		diff=1
	fi

	if [ "$diff" = 1 ]; then
		setup_diff_options
	fi

	if [ "$use_ai" = 1 ]; then
		ai_enhanced_diff "$@"
	else
		diff_them "$@"
	fi
}

setup_diff_options() {
	diff_options=()
	if [ "$ignore_case" = 1 ]; then
		diff_options+=(-i)
	fi
	if [ "$ignore_whitespace" = 1 ]; then
		diff_options+=(-w)
	fi
	if [ "$use_color" = 1 ]; then
		diff_options+=("--color")
	fi

	case "$output_format" in
	unified)
		diff_options+=(-u"$context_lines")
		;;
	side-by-side)
		diff_options+=(-y -W"$(tput cols)")
		;;
	context)
		diff_options+=(-c"$context_lines")
		;;
	*)
		die "Unknown output format: $output_format"
		;;
	esac
}

diff_them() {
	# For now we don't have a good n-way diff tool, see future/ndiff
	# so we will do pairwise diff against the first (main) argument.
	local main_file="$1"
	shift
	for file in "$@"; do
		diff "${diff_options[@]}" "$main_file" "$file"
	done
}

ai_enhanced_diff() {
	local files=("$@")
	local prompt=""

	if [ "$economy" = 1 ]; then
		prompt="Please highlight the differences between the files."
	else
		prompt="Please compare the files: highlight similarities and differences."
	fi

	{
		if [ "$economy" != 1 ]; then
			cat-named "${files[@]}"
		fi

		if [ "$diff" = 1 ]; then
			echo
			echo "#Diffs"
			echo
			diff_them "${files[@]}"
		fi
	} | process -m="$model" "$prompt"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	diffy "$@"
fi

# version: 0.1.0

# FIXME: Improve error handling for non-existent files
# TODO: Add support for directory comparison
# TODO: Consider adding an option for word-level diff
