#!/usr/bin/env bash

# [file list]
# Summarizes files, running executables with --help or showing file heads

rundown() {
	local timeout= t=3   # timeout in seconds
	local min_lines= m=4 # minimum number of lines for valid help output

	eval "$(ally)"

	while IFS= read -r file; do
		echo "## $file"
		echo
		if [ -x "$file" ]; then
			process_executable "$file"
		elif [[ "$(file -b --mime-type "$file")" == text/* ]]; then
			process_text "$file"
		else
			process_binary "$file"
		fi
		echo
		echo
	done
}

process_executable() {
	local file=$1
	temp_file=$(mktemp)
	trap 'rm -f "$temp_file"' EXIT

	# prepend ./ if needed
	if ! [[ "$file" == */* ]]; then
		exe="./$file"
	else
		exe=$file
	fi

	if timeout "$timeout" "$exe" --help >"$temp_file" 2>&1; then
		output=$(head -n "$((min_lines + 1))" "$temp_file")
		lines=$(echo "$output" | wc -l)
		if [ "$lines" -ge "$min_lines" ]; then
			echo "$output"
		else
			printf >&2 "BAD\t%s\tNot enough help lines\n" "$file"
			head "$file"
		fi
	else
		exit_status=$?
		if [ $exit_status -eq 124 ] || [ $exit_status -eq 137 ]; then
			printf >&2 "BAD\t%s\tTimed out\n" "$file"
		else
			printf >&2 "BAD\t%s\tExit status: %d\n" "$file" "$exit_status"
		fi
		head "$file"
	fi
}

process_text() {
	head "$file"
}

process_binary() {
	file -b "$file"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	rundown "$@"
fi
