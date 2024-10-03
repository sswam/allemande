#!/bin/bash

# [file] "instructions to improve it" [reference files ...]
# Improve something using AI
set -e -u -o pipefail

improve() {
	local model= m=	# model
	local style= s=0	# refer to hello.<ext> for style
	local edit= e=1	# do not edit
	local use_ai= a=1	# use AI, can turn off for testing with -a=0
	local concise= c=0	# concise
	local basename= b=0	# use basenames
	local test= t=1	# run tests if found (default: on)
	local testok= T=0	# tests are okay, don't change
	local codeok= C=0	# code is okay, don't change
	local changes= S=1	# allow changes to existing functionality or API changes
	local features= F=1	# allow new features
	local lint= L=1	# run linters and type checkers if possible
	local format= F=1	# format code
	local writetest= w=1	# write tests if none found
	local numline= n=1	# number lines

	eval "$(ally)"

	local file=$1
	local prompt=${2:-}
	shift 2 || shift 1 || true
	local refs=("$@")

	if (( "$basename" )); then
		opt_b=("-b")
	else
		opt_b=()
	fi

	# -C or -T options imply -t
	if (( "$codeok" )) || (( "$testok" )); then
		test=1
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
	if (( "$format" )); then
		{ formy "$file" || true; } | tee -a "$results_file"
	fi

	# Lint and type check
	if (( "$lint" )); then
		{ linty "$file" || true; } | tee -a "$results_file"
	fi

	# Find and run tests
	local tests_file=""
	local test_results=""
	local test_ext="bats"

	if (( "$test" )); then
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
		if (( "testok" )); then
			checks_prompt="Some checks failed. The tests are correct, so don't change them; please fix the main program code."
		elif (( "codeok" )); then
			checks_prompt="Some checks failed. The main program code is correct, so don't change it; please fix the tests."
		else
			checks_prompt="Some checks failed. Please fix the program and/or the tests. If the code looks correct as it is, please update the tests to match the code, or add comments to disable certain linting behaviour, etc."
		fi
	elif [ "$tests_file" ]; then
		echo >&2 "Checks passed"
		checks_prompt="Our checks passed."
		rm "$results_file"
		test=""
	elif (( "$test" )); then
		echo >&2 "No tests found"
		if (( "$writetest" )); then
			# tests "$file"
			checks_prompt="No tests found. Please write some tests."
		fi
		test=""
	fi

	# style reference and prompt for - option
	style_ref="hello_$ext.$ext"
	if (( "$style" = 1 )) && [ "$(which "$style_ref")" ]; then
		echo >&2 "Using style reference: $style_ref"
		refs+=("$style_ref")
		prompt="in the style of \`$style_ref\`, $prompt"
	fi

	tests_name_clause=""
	if [ -f "$tests_file" ] && [ -s "$tests_file" ]; then
		tests_name_clause=" and/or \`$tests_file\`"
	fi

	prompt="Please improve \`$base\`$tests_name_clause, and bump the patch version if present, $prompt. Add a header line \`#File: filename\` before each file's code. Comment on your changes at the end, not inline. $checks_prompt"

	if (( "$changes" = 0 )); then
		prompt="$prompt. Strictly no changes to existing functionality or APIs."
	fi

	if (( "$features" = 0 )); then
		prompt="$prompt. Strictly no new features."
	fi

	if (( "$concise" )); then
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

	if ((!"$use_ai")); then
		function process() { nl; }
	fi

	# Process input and save result
	printf "%s\n" "$input" | v process -m="$model" "$prompt" |
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
	if (( "$edit" )); then
		if [ -n "$tests_file" ]; then
			vim -d "$file~" "$file" -c "botright vnew $tests_file"
		else
			vimdiff "$file~" "$file"
		fi
	fi

	# if using -t but not -C or -T, it may edit the code and/or the tests, so we don't automatically replace the old version with the new one
	confirm=""
	if (( "$tests" )) && (( "$codeok" = 0 )) && (( "$testok" = 0 )); then
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
