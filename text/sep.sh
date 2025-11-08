#!/usr/bin/env bash

# [file ...]
# Split files using AI or apply splits from stdin

sep-sh() {
	local analyze_only= a=     # only analyze, output split plan to stdout
	local apply_only= A=       # only apply splits from stdin
	local model= m=            # LLM model
	local prompt= p=           # custom prompt for splitting

	eval "$(ally)"

	# Validate mode combination
	if [ "$analyze_only" = 1 ] && [ "$apply_only" = 1 ]; then
		die "cannot use both --analyze-only and --apply-only"
	fi

	# Default mode: both analyze and apply
	if [ "$apply_only" = 1 ]; then
		apply-splits
	elif [ "$analyze_only" = 1 ]; then
		analyze-files "$@"
	else
		# Both: analyze then apply
		local split_plan
		split_plan=$(analyze-files "$@")
		printf -- "%s\n" "$split_plan" | apply-splits
	fi
}

analyze-files() {
	local files=("$@")

	# Handle stdin if no files provided
	if [ "${#files[@]}" -eq 0 ]; then
		files=(/dev/stdin)
	fi

	# Build input with line numbers for AI
	local numbered_input
	numbered_input=$(mktemp)
	trap 'rm -f "$numbered_input"' EXIT

	for file in "${files[@]}"; do
		echo "=== File: $file ==="
		nl -ba -nln -w1 -s$'\t' "$file"
		echo
	done > "$numbered_input"

	# Default prompt if none provided
	local analysis_prompt=${prompt:-"Analyze the provided files and determine how to split them into logical, cohesive units for refactoring. Consider:
- Functions or classes that should be in separate files
- Related code that should stay together
- Logical module boundaries
- Import dependencies

Output your split plan in this exact format for each section:

filename:\tnew/path/to/file.ext
source:\toriginal/file/path
start:\t<line_number>
end:\t<line_number>
description:\tbrief description of what this section contains
\tcan continue on multiple lines
\teach continuation indented with single tab

(blank line between records)

Multiple sections can share the same filename if they should be combined.
Include necessary imports/headers for each new file."}

	process -m="$model" "$analysis_prompt" < "$numbered_input"
}

apply-splits() {
	local current_record=()
	local all_records=()
	local line

	# Parse records from stdin
	while IFS= read -r line; do
		if [ -z "$line" ]; then
			# Blank line = end of record
			if [ "${#current_record[@]}" -gt 0 ]; then
				all_records+=("$(printf '%s\n' "${current_record[@]}")@@@RECORD@@@")
				current_record=()
			fi
		else
			current_record+=("$line")
		fi
	done

	# Don't forget last record
	if [ "${#current_record[@]}" -gt 0 ]; then
		all_records+=("$(printf '%s\n' "${current_record[@]}")@@@RECORD@@@")
	fi

	# Process each record
	local record
	for record in "${all_records[@]}"; do
		process-record "$record"
	done
}

process-record() {
	local record_text=$1
	local filename= source= start= end= description=
	local in_continuation=0
	local current_key=
	local line

	# Parse key:value pairs
	while IFS= read -r line; do
		if [[ "$line" =~ ^[[:space:]].*$ ]]; then
			# Continuation line (starts with whitespace)
			if [ -n "$current_key" ]; then
				case "$current_key" in
				filename) filename+=$'\n'"$line" ;;
				source) source+=$'\n'"$line" ;;
				description) description+=$'\n'"$line" ;;
				esac
			fi
		elif [[ "$line" =~ ^([^:]+):[[:space:]]*(.*)$ ]]; then
			# Key:value line
			local key="${BASH_REMATCH[1]}"
			local value="${BASH_REMATCH[2]}"
			current_key="$key"

			case "$key" in
			filename) filename="$value" ;;
			source) source="$value" ;;
			start) start="$value" ;;
			end) end="$value" ;;
			description) description="$value" ;;
			esac
		fi
	done < <(printf '%s\n' "$record_text" | grep -v '@@@RECORD@@@')

	# Validate required fields
	if [ -z "$filename" ] || [ -z "$source" ] || [ -z "$start" ] || [ -z "$end" ]; then
		echo >&2 "skipping incomplete record: filename='$filename' source='$source' start='$start' end='$end'"
		return
	fi

	# Extract and append content
	extract-lines "$source" "$start" "$end" "$filename"

	if [ -n "$description" ]; then
		echo >&2 "extracted lines $start-$end from $source -> $filename: $description"
	else
		echo >&2 "extracted lines $start-$end from $source -> $filename"
	fi
}

extract-lines() {
	local source=$1
	local start=$2
	local end=$3
	local output=$4

	# Ensure output directory exists
	local output_dir
	output_dir=$(dirname "$output")
	mkdir -p "$output_dir"

	# Extract lines and append to output file
	# Using sed for line range extraction
	if [ -f "$source" ]; then
		sed -n "${start},${end}p" "$source" >> "$output"
		echo >> "$output"  # Add blank line between sections
	else
		echo >&2 "source file not found: $source"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	sep-sh "$@"
fi

# version: 0.1.0

# <think>
# Let me understand what's needed:
#
# 1. A tool called `sep.sh` (separate/split) that:
# 			- Takes file(s) and uses AI to determine how to split them (e.g., for refactoring)
# 			- Numbers lines first
# 			- Feeds whole files to LLM
# 			- Outputs in key:\tvalue format with blank lines between records
# 			- Can apply the splits automatically or separately
#
# 2. Three modes:
# 			- Default: both analyze with AI and apply splits
# 			- Analyze only: output to stdout
# 			- Apply only: read from stdin
#
# 3. Output format for each section:
# 			- filename: new file path
# 			- source: original file
# 			- start: line number
# 			- end: line number
# 			- Extra headers as needed
# 			- Continued lines indented with single tab
#
# 4. Multiple sections can go into one output file (multiple records for same filename)
#
# Let me design this:
# - Use `process` for AI interaction
# - Number lines when feeding to AI
# - Parse the AI output (key:value format)
# - Apply splits by reading source files and extracting line ranges
# - Support both combined and separate modes
#
# The key:value format with tab separator is straightforward to parse and generate.
# </think>
