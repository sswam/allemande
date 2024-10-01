#!/bin/bash

# [log_dir] [--add-timestamps] [--output-dir=<dir>]
# Sort LLM log files by time, grouping prompt and answer files

llm_log_sort() {
	local log_dir=~/llm.log
	local add_timestamps=
	local output_dir=

	. opts

	# Non-option arguments
	if [ $# -gt 0 ]; then
		log_dir="$1"
	fi

	# Strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	if [ ! -d "$log_dir" ]; then
		echo >&2 "Error: Log directory does not exist: $log_dir"
		return 1
	fi

	# Create temporary directory for processing
	local temp_dir=$(mktemp -d)
	trap 'rm -rf "$temp_dir"' EXIT

	# Process files
	find "$log_dir" -type f | while read -r file; do
		local basename=$(basename "$file")
		local prefix=${basename%%.*}
		local timestamp=${basename##*.}

		if [[ $basename =~ ^prompt\. ]]; then
			# Handle prompt files
			cp "$file" "$temp_dir/${timestamp}_prompt_$prefix"
		elif [[ $basename =~ ^answer\. ]]; then
			# Handle answer files
			cp "$file" "$temp_dir/${timestamp}_answer_$prefix"
		else
			# Handle files without prompt/answer prefix
			local new_prompt="$temp_dir/${timestamp}_prompt_$prefix"
			cp "$file" "$temp_dir/${timestamp}_answer_$prefix"
			touch "$new_prompt"
			echo "Generated prompt: $prefix" > "$new_prompt"
		fi
	done

	# Sort and group files
	local sorted_files=$(ls -1tr "$temp_dir")
	local current_prefix=""
	local current_timestamp=""

	echo "$sorted_files" | while read -r file; do
		local prefix=${file#*_*_}
		local timestamp=${file%%_*}
		local type=${file#*_}
		type=${type%%_*}

		if [ "$prefix" != "$current_prefix" ]; then
			current_prefix="$prefix"
			current_timestamp="$timestamp"
		fi

		local output_file="$log_dir/${type}.${prefix}"
		if [ "$add_timestamps" = "1" ]; then
			output_file="${output_file}.${current_timestamp}"
		fi

		cp "$temp_dir/$file" "$output_file"

		if [ "$type" = "answer" ]; then
			touch -d "@$(($(date -d "@$current_timestamp" +%s) + 1))" "$output_file"
		else
			touch -d "@$current_timestamp" "$output_file"
		fi
	done

	echo "Files sorted and grouped successfully."

	# Restore caller options
	eval "$old_opts"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	llm_log_sort "$@"
fi
