#!/bin/bash

# [file] "instructions to improve it" [reference files ...]
# Improve something using AI
set -e -u -o pipefail

improve() {
	local m=  # model
	local s=0 # refer to hello.<ext> for style
	local E=0 # do not edit
	local c=0 # concise
	local b=0 # use basenames
	local t=1 # run tests if found (default: on)
	local T=0 # tests are perfect
	local C=0 # code is perfect
	local S=0 # strictly no changes to existing functionality or API changes
	local F=0 # strictly no new features
	local L=1 # run linters and type checkers if possible
	local F=1 # format code
	local w=1 # write tests if none found

	eval "$(ally)"

	local file=$1
	local prompt=${2:-}
	shift 2 || shift 1 || true
	local refs=("$@")

	if [ "$b" = 1 ]; then
		opt_b=("-b")
	else
		opt_b=()
	fi

	# -C or -T options imply -t
	if [ "$C" = 1 -o "$T" = 1 ]; then
		t=1
	fi

	# Check if the file exists
	if [ ! -e "$file" ]; then
		local prog2=$(which "$file")
		if [ ! -e "$prog2" ]; then
			echo >&2 "not found: $file"
			exit 1
		fi
		file=$prog2
	fi

	# resolve symlinks
	file=$(readlink -f "$file")

	# files and directories
	local dir=$(dirname "$file")
	local base=$(basename "$file")
	#	local name=${base%.*}
	local ext=${file##*.}
	if [ "$ext" == "$base" ]; then
		ext="sh"
	fi

	# Results file for checks and tests
	local results_file="$dir/$base.results.txt"
	if [ -e "$results_file" ]; then
		move-rubbish "$results_file"
	fi

	checks_prompt=""

	# Reformat code
	if [ "$F" = 1 ]; then
		{ formy "$file" || true; } | tee -a "$results_file"
	fi

	# Lint and type check
	if [ "$L" = 1 ]; then
		{ linty "$file" || true; } | tee -a "$results_file"
	fi

	# Find and run tests
	local tests_file=""
	local test_results=""
	local test_ext="bats"

	if [ "$t" = 1 ]; then
		tests_results=$(testy "$file" || true)
		tests_file=$(printf "%s" "$tests_results" | head -n 1)
		printf "%s" "$tests_results" | tail -n +2 | tee -a "$results_file"
	fi

	if [ -s "$results_file" ]; then
		echo >&2 "Checks failed: $results_file"
		if [ -n "$tests_file" ]; then
			refs+=("$tests_file")
		fi
		refs+=("$results_file")
		if [ "$T" = 1 ]; then
			checks_prompt="Some checks failed. The tests are correct, so don't change them; please fix the main program code."
		elif [ "$C" = 1 ]; then
			checks_prompt="Some checks failed. The main program code is correct, so don't change it; please fix the tests."
		else
			checks_prompt="Some checks failed. Please fix the program and/or the tests. If the code looks correct as it is, please update the tests to match the code, or add comments to disable certain linting behaviour, etc."
		fi
	elif [ "$tests_file" ]; then
		echo >&2 "Checks passed"
		checks_prompt="Our checks passed."
		rm "$results_file"
		t=""
	elif [ "$t" = 1 ]; then
		echo >&2 "No tests found"
		if [ -n "$w" ]; then
			# tests "$file"
			checks_prompt="No tests found. Please write some tests."
		fi
		t=""
	fi

	# style reference and prompt for -s option
	style="hello_$ext.$ext"
	if [ "$s" = 1 -a -n "$(which "$style")" ]; then
		echo >&2 "Using style reference: $style"
		refs+=("$style")
		prompt="in the style of \`$style\`, $prompt"
	fi

	tests_name_clause=""
	if [ -f "$tests_file" ] && [ -s "$tests_file" ]; then
		tests_name_clause=" and/or \`$tests_file\`"
	fi

	prompt="Please improve \`$base\`$tests_name_clause, and bump the patch version if present, $prompt. Add a header line \`#File: filename\` before each file's code. Comment on your changes at the end, not inline. $checks_prompt"

	if [ "$S" = 1 ]; then
		prompt="$prompt. Strictly no changes to existing functionality or APIs."
	fi

	if [ "$F" = 1 ]; then
		prompt="$prompt. Strictly no new features."
	fi

	if [ "$c" = 1 ]; then
		prompt="$prompt, Please reply concisely with only the changes."
	fi

	local input=$(v cat-named -p "${opt_b[@]}" "$file" "${refs[@]}")

	# Backup original file
	if [ -e "$file~" ]; then
		move-rubbish "$file~"
	fi
	echo n | cp -i -a "$file" "$file~" # WTF, there's no proper no-clobber option?!

	comment_char="#"
	case "$ext" in
	c | cpp | java | js | ts | php | cs | go | rs)
		comment_char="//"
		;;
	sh | py | pl | rb)
		comment_char="#"
		;;
	md | txt)
		comment_char=""
		;;
	esac

	target_file="$file"
	output_file="$file~"

	# By default, it should edit the main code.
	# if using -C option, it must edit the tests, so the output file is the tests file plus a tilde
	if [ "$C" = 1 ]; then
		target_file="$tests_file"
		output_file="$tests_file~"
	fi

	# Process input and save result
	printf "%s\n" "$input" | process -m="$m" "$prompt" |
		if [ -n "$comment_char" ]; then
			markdown_code.py -c "$comment_char"
		else
			cat
		fi >"$file~"

	# check not empty
	if [ ! -s "$file~" ]; then
		echo >&2 "empty output"
		rm "$file~"
		exit 1
	fi

	# Compare original and improved versions
	if [ "$E" = 0 ]; then
		if [ -n "$tests_file" ]; then
			vim -d "$file~" "$file" -c "botright vnew $tests_file"
		else
			vimdiff "$file~" "$file"
		fi
	fi

	# if using -t but not -C or -T, it may edit the code and/or the tests, so we don't automatically replace the old version with the new one
	confirm=""
	if [ "$t" = 1 -a "$C" = 0 -a "$T" = 0 ]; then
		confirm="confirm" # means it might have edited either or both files
	fi

	# Swap in the hopefully improved version
	# Use swapfiles with -c option to preserve hardlinks
	$confirm swapfiles -c "$target_file" "$output_file" ||
		# maybe the new version is an improved tests file
		if [ $confirm ] && [ "$target_file" = "$file" ]; then
			$confirm swapfiles -c "$tests_file" "$output_file"
		fi

	# In the case that it edited both files, the user should have figured it out in their editor,
	# we can't handle that automatically yet.
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	improve "$@"
fi
