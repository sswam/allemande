#!/usr/bin/env bash
# [program ...]
# Test a program with its tests

testy() {
	local verbose= v=0	# verbose mode, output results when all tests pass
	local timeout= t=10	# timeout (per test, Python only at the moment)
	local debug= d=         # run test with debug option to show logs and stdout

	eval "$(ally)"

	if (( $# != 1 )); then
		each testy -v="$v" -t="$t" -d="$d" : "$@"
		return $?
	fi

	(
		local prog="$(finder "$1")"
		if [ ! -f "$prog" ]; then
			echo >&2 "File not found: $1"
			return 1
		fi

		# Some tests assume we are in the program directory
		# TODO I think there was some problem with doing this, I should have noted what it was...
		cd "$(dirname "$prog")"

		prog_basename="$(basename "$prog")"

		# Get the extension of the program
		local ext="${prog##*.}"
		if [[ $prog != *.* ]]; then
			ext="sh"
		fi

		# handle Perl modules
		if [ "$ext" = pm ]; then
			ext=pl
		fi
		local test_ext="$ext"

		# avoid binary files
		if [[ $(file --mime-encoding -b "$prog") == "binary" ]]; then
			echo >&2 "Binary file, not testing."
			return 0
		fi

		if [ "$ext" == "sh" ]; then
			test_ext="bats"
		fi
		# If prog path contains tests, or prog is test_* or *_test.*, use the prog as the tests_file
		if [[ "$prog" == tests/* ]] || [[ "$prog" == */tests/* ]] || [[ "$prog_basename" == test_* ]] || [[ "$prog_basename" == *_test.* ]]; then
			local tests_file="$prog"
		elif [ "$ext" = rs ]; then
			local tests_file="$prog"
		else
			# For Go and general cases, find the test file by searching.
			local base
			base=$(basename "$prog" ".$ext")
			local test_dir
			# For Go, tests are typically in the same directory.
			if [ "$ext" = go ]; then
				test_dir="$(dirname "$prog")"
			# For other languages, assume a tests/ subdirectory.
			else
				test_dir="$(dirname "$prog")/tests"
			fi

			# Try the expected naming convention first
			local tests_file="$test_dir/${base}_test.$test_ext"

			if [ ! -f "$tests_file" ]; then
				# Use an array to safely capture glob results. This prevents errors if no file matches.
				local test_files=( "$test_dir"/"${base}"_test.* )

				# Warn if multiple test files are found
				if (( ${#test_files[@]} > 1 )); then
					echo >&2 "Warning: Multiple test files found for $prog. Using the first match: ${test_files[*]}"
				fi

				# Check if the glob found an actual file (and not just the unexpanded pattern).
				if [ -f "${test_files[0]}" ]; then
					# If a test file is found, use the first match.
					tests_file="${test_files[0]}"
				fi
			fi
		fi
		if [ ! -f "$tests_file" ]; then
			echo >&2 "Tests file not found: $tests_file"
			return 1
		fi
		printf "%s\n" "$tests_file"

		local output_file="$prog.test"

		# call calls a function, but won't run a tool
		call "test_$ext" "$tests_file" 2>&1 | tee "$output_file"
	)
}

run() {
	if (( verbose )); then
		v "$@"
	else
		v quiet-on-success "$@" 2>/dev/null
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
	local debug_opts=()
	if (( debug )); then
		debug_opts=(--log-cli-level=DEBUG --capture=tee-sys)
	fi
	if COLUMNS=80 run pytest "${debug_opts[@]}" --timeout="$timeout" --asyncio-mode=auto -vv --capture=no --tb=short --disable-warnings --no-header "$tests_file" >"$results" 2>&1; then
		if (( verbose )); then
			cat "$results"
		fi
		rm "$results"
		return 0
	fi
	if (( verbose )) || grep "=== ERRORS ===" "$results"; then
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
	run make "${tests_file%.c}" && run "${tests_file%.c}" || return 1
}

test_pl() {
	local tests_file="$1"
	run prove -v "$tests_file" || return 1
}

test_go() {
	local tests_file="$1"
	run go test || return 1
}

test_rs() {
	local tests_file="$1"
	# run cargo test --manifest-path "$tests_file" || return 1
	run cargo test --bin "$(basename -s .rs "$tests_file")" || return 1
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
