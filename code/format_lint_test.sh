#!/usr/bin/env bash

# [file ...]
# Format, lint, and test files
# Performs formatting, linting, and testing on specified files

format-lint-test() {
	verbose= v=      # enable verbose output
	quiet= q=        # suppress output on success

	eval "$(ally)"

	files="$@"       # array of files to process

	local fail=()

	for file in "${files[@]}"; do
		printf "%s\n" "# Checking: $file"
		quiet-on-success verbose formy "$file" 2>&1 || fail+=("$file")
		quiet-on-success verbose linty "$file" 2>&1 || fail+=("$file")
		quiet-on-success verbose testy "$file" 2>&1 || fail+=("$file")
		echo
	done

	if [ ${#fail[@]} -gt 0 ]; then
		printf "%d\n" "${#fail[@]}"
		# unique
		mapfile -t fail < <(printf "%s\n" "${fail[@]}" | uniqo)
		printf "%s\n" "${fail[@]}"
		return 1
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	format-lint-test "$@"
fi

# version: 0.1.3
