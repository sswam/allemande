#!/usr/bin/env bash

# [file list]
# Summarizes files, running executables with --help or showing file heads

rundown() {
	local timeout=3           # timeout in seconds
	local min_lines=4         # minimum number of lines for valid help output
	local number_headers= n=  # number entries

	eval "$(ally)"

	local counter=1

	while IFS= read -r file; do
		if ((number_headers)); then
			printf "## %d. %s\n" "$counter" "$file"
			((counter++))
		else
			printf "## %s\n" "$file"
		fi
		echo

		if [ -d "$file" ]; then
			process_directory "$file"
		elif [ -L "$file" ]; then
			process_symlink "$file"
		elif [[ "$(file -b --mime-type "$file")" != text/* ]]; then
			process_binary "$file"
		elif [ -x "$file" ]; then
			process_text_executable "$file"
		else
			process_text "$file"
		fi
		echo
		echo
	done
}

process_text_executable() {
	local file=$1
	local temp_file
	local exe
	local exit_status

	temp_file=$(mktemp)
	trap 'rm -f "$temp_file"' EXIT

	# prepend ./ if needed
	if [[ "$file" == */* ]]; then
		exe=$file
	else
		exe="./$file"
	fi

	if timeout "$timeout" "$exe" --help >"$temp_file" 2>&1; then
		local output
		output=$(head -n "$((min_lines + 1))" "$temp_file")
		local lines
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
	file -b "$file" --mime-type
	file -b "$file"
}

process_symlink() {
	local file=$1
	local target
	target=$(readlink -f "$file")
	printf "Symlink to: %s\n" "$target"
}

process_directory() {
	local file=$1
	local count
	count=$(find "$file" -maxdepth 1 | wc -l)
	printf "Directory of %s entries\n\n" "$((count - 1))"
	ls -F "$file"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	rundown "$@"
fi

# version: 0.1.1
