#!/bin/bash

# Freedom.sh
# Version: 0.1.2

# [codebase path] [output path]
# Clones a codebase while avoiding copyright issues and making improvements

freedom() {
	local model="" m=""	# AI model to use
	local verbose="" v=""  # Enable verbose output
	local prompt="" p=""  # Extra guidance prompt

	. opts  # Load options into the above vars

	# Strict mode
	local old_opts
	old_opts=$(set +o)
	set -euo pipefail

	# Support long and short options
	model=${model:-$m}
	verbose=${verbose:-$v}

	# Non-option arguments
	local input_path=${1:-}
	local output_path=${2:-}

	if [ -z "$input_path" ] || [ -z "$output_path" ]; then
		echo >&2 "Error: Both input and output paths are required."
		return 1
	fi

	if [ ! -d "$input_path" ]; then
		echo >&2 "Error: Input path is not a directory."
		return 1
	fi

	mkdir -p "$output_path"

	local IFS=$'\n'
	local files
	files=( $(find "$input_path" -type f) )

	code-doc --model "$model" --prompt "$prompt" "${files[@]}"

	for file in "${files[@]}"; do
		suggest_improvements "$file.md" "$prompt" > "$file.suggestions.md"
	done

	# TODO in dependency order, bottom-up
	for file in "${files[@]}"; do
		output_file="$output_path/$(realpath --relative-to "$input_path" "$file")"
		translate_file "$output_path" "$file" "$file.suggestions.md" "$prompt"
	done

	echo >&2 "Translation completed. Output saved to $output_path"

	eval "$old_opts"
}

translate_file() {
	local output_file=$1
	local input_file=$2
	local suggestions=$3
	local prompt=$4

	mkdir -p "$(dirname "$output_file")"

	local prompt="Translate this code to an equivalent implementation,
avoiding copyright issues. Rename functions with better names,
improve APIs where possible (as suggested), but maintain overall functionality.
Do not quote any code exactly.
$prompt	
Here's the original code, its documentation, and the suggested improvements:"

	cat-named "$input_file" "$input_file.md" "$suggestions" |
	process -m="$model" "$prompt" > "$output_file"
}

suggest_improvements() {
	local file=$1

	local prompt="Suggest improvements for this code, focusing on:
1. Simplicity
2. Clarity
3. Generality
4. Modularity
5. Error handling and security
4. Performance
5. Any other improvements
Provide concise, actionable suggestions.
$prompt"

	< "$file" process -m="$model" "$prompt"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	freedom "$@"
fi
