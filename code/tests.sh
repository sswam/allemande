#!/bin/bash

# <program to test> "instructions to create tests" [reference files ...]
# Generate tests for a program using AI

tests() {
	local m=    # model
	local s=1   # refer to test_hello.py for test style

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	local program=$1
	local prompt=$2
	shift 2
	local refs=("$@")

	local dir=$(dirname "$program")
	local base=$(basename "$program")
	local stem=${base%.*}

	local ext=.${program##*.}
	if [ "$ext" == ".$base" ]; then
		ext=".sh"
	fi

	mkdir -p "$dir/tests"

	tests_ext=$ext

	case "$ext" in
	.sh)
		tests_ext=.bats
		;;
	esac

	local test_file="$dir/tests/test_{$stem}$tests_ext"

	# Check if test file already exists
	if [ -e "$test_file" ]; then
		echo >&2 "already exists: $test_file"
		exit 1
	fi

	# Test style reference and prompt for -s option
	if [ "$s" = 1 ]; then
		refs+=("test_hello$ext")
		prompt="in the style of \`test_hello$tests_ext\`, $prompt"
	fi

	prompt="Please write \`test_$base\` to test \`$base\`, $prompt"

	local input=$(cat_named.py -p -b "$program" "${refs[@]}")

	if [ -z "$input" ]; then
		input=":)"
	fi

	# Process input and save result
	printf "%s\n" "$input" | process -m="$m" "$prompt" | markdown_code.py -c '#' > "$test_file"

	vi -O "$test_file" "$program"

	# restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	tests "$@"
fi
