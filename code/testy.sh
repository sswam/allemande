#!/bin/bash
# [program ...]
# Test a program with its tests

. each

test_sh() {
	local tests_file="$1"
	quiet bats -t "$tests_file" | { grep -v '^ok ' || true; }
	return ${PIPESTATUS[0]}
}

test_py() {
	local tests_file="$1"
	quiet pytest -q --tb=short --disable-warnings --show-capture=no --no-header "$tests_file" 2>/dev/null || return 1
}

test_c() {
	local tests_file="$1"
	quiet googletest "$tests_file" || return 1
}

test_pl() {
	local tests_file="$1"
	quiet prove -v "$tests_file" || return 1
}

test_go() {
	local tests_file="$1"
	quiet go test "$tests_file" || return 1
}

test_rs() {
	local tests_file="$1"
	quiet cargo test --manifest-path "$tests_file" || return 1
}

test_js() {
	local tests_file="$1"
	quiet jest "$tests_file" || return 1
}

test_ts() {
	test_js "$@" || return 1
}

testy() {
	local prog="$1"
	local ext="${prog##*.}"
	if [[ $prog != *.* ]]; then
		ext="sh"
	fi
	local test_ext="$ext"
	if [ "$ext" == "sh" ]; then
		test_ext="bats"
	fi
	local tests_file="$(dirname "$prog")/tests/$(basename "$prog" ".$ext")_test.$test_ext"
	if [ ! -f "$tests_file" ]; then
		echo >&2 "Tests file not found: $tests_file"
		return 1
	fi
	"test_$ext" "$tests_file"
}

if [ "$BASH_SOURCE" == "$0" ]; then
	each testy : "$@"
fi
