#!/usr/bin/env bash
# [program ...]
# Test a program with its tests

testy() {
	local verbose= v=0	# verbose mode, output results when all tests pass
	local timeout= t=10	# timeout (per test, Python only at the moment)

	eval "$(ally)"

	if (( $# != 1 )); then
		each testy : "$@"
		return $?
	fi

	(
		local prog="$(finder "$1")"
		cd "$(dirname "$prog")"
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
		printf "%s\n" "$tests_file"
		"test_$ext" "$tests_file"
	)
}

run() {
	if (( verbose )); then
		v "$@"
	else
		v quiet "$@" 2>/dev/null
	fi
}

test_sh() {
	local tests_file="$1"
	run bats -t --print-output-on-failure "$tests_file" | { grep -v '^ok ' || true; }
	return ${PIPESTATUS[0]}
}

test_py() {
	local tests_file="$1"
	results=$(mktemp)
	if COLUMNS=80 run pytest --timeout=$timeout --asyncio-mode=auto -vv --capture=no --tb=short --disable-warnings --no-header "$tests_file" >"$results" 2>&1; then
		rm "$results"
		return 0
	fi
	if grep "=== ERRORS ===" "$results"; then
		cat "$results"
	else
		# Just keep the important part of the output
		<"$results" sed -e '/===.*test session starts/,/===/{/===.*test session starts/d; /===/!d;}' -e '/===.*short test summary info/,$d'
		rm "$results"
	fi
	return 1
}

test_c() {
	local tests_file="$1"
	run googletest "$tests_file" || return 1
}

test_pl() {
	local tests_file="$1"
	run prove -v "$tests_file" || return 1
}

test_go() {
	local tests_file="$1"
	run go test "$tests_file" || return 1
}

test_rs() {
	local tests_file="$1"
	run cargo test --manifest-path "$tests_file" || return 1
}

test_js() {
	local tests_file="$1"
	run jest "$tests_file" || return 1
}

test_ts() {
	test_js "$@" || return 1
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	testy "$@"
fi
