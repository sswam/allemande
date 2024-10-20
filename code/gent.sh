#!/bin/bash

# <program to test> "instructions to create tests" [reference files ...]
# Generate tests for a program using AI

tests() {
	local m=    # model
	local s=1   # refer to test_hello.py for test style
	local E=0   # do not edit

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	local program=$1
	local prompt=${2:-}
	shift 2 || shift 1 || true
	local refs=("$@")

	if [ ! -e "$program" ]; then
		program=$(readlink -f "$(which-file "$program")")
	fi

	local dir=$(dirname "$program")
	local base=$(basename "$program")
	local stem=${base%.*}

	local ext=${base##*.}
	if [ "$ext" == "$base" ]; then
		ext="sh"
	fi

	mkdir -p "$dir/tests"

	tests_ext=$ext

	executable=0
	case "$ext" in
	sh)
		tests_ext=bats
		executable=1
		if [ ! -e "$dir/tests/test_helper" ] && [ -d "/usr/lib/bats/bats-support" ]; then
			ln -s /usr/lib/bats "$dir/tests/test_helper"
		fi
	esac

	local tests_base="${stem}_test.$tests_ext"
	local tests_path="$dir/tests/$tests_base"

	# Check if test file already exists
	if [ -s "$tests_path" ]; then
		echo >&2 "already exists: $tests_path"
		exec improve "$tests_path" "Please improve the tests, fixing and adding test cases as needed." "$program" "${refs[@]}"
		exit 1
	fi

	# Test style reference and prompt for -s option
	if [ "$s" = 1 ]; then
		local hello="hello_$ext.$tests_ext"
		hello=$(which-file "$hello")
		if [ -n "$hello" ]; then
			dir=$(dirname "$hello")
			example="$dir/tests/hello_${ext}_test.$tests_ext"
			refs+=("$example")
			prompt="in the style of \`$example\`, $prompt"
		fi
	fi

	prompt="Please write \`$tests_base\` to test \`$base\`, $prompt"

	local input=$(cat-named -p -b "$program" "${refs[@]}")

	if [ -z "$input" ]; then
		input=":)"
	fi

	# Process input and save result
	printf "%s\n" "$input" | process -m="$m" "$prompt" | markdown-code -c '#' > "$tests_path"

	if [ "$executable" = 1 ]; then
		chmod +x "$tests_path"
	fi

	if [ "$E" = 0 ]; then
		$EDITOR -O "$tests_path" "$program"
	fi

	testy "$program"

	# restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	tests "$@"
fi
