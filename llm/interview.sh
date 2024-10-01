#!/bin/bash

# [user's name]
# Conducts an AI interview, logging the chat and summarizing chunks

interview() {
	local model= m=    # LLM model
	local timeout= t=60	# Idle timeout in seconds
	local plan_file= p=	# File containing interview plan/goals

	. opts  # Note to AI: This magically loads options into the above vars

	# Support long and short options
	model=${model:-$m}
	timeout=${timeout:-$t}
	plan_file=${plan_file:-$p}

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	local user_name=${1:-Anonymous}
	local chat_log="chat_log_$(date +%Y%m%d_%H%M%S).txt"
	local summary_log="summary_log_$(date +%Y%m%d_%H%M%S).txt"
	local total_summary="total_summary.txt"
	local chunk_count=0
	local blank_line_count=0
	local chunk_content=""

	# Initialize or read existing total summary
	[ -f "$total_summary" ] || echo "No previous sessions." > "$total_summary"

	# Main interview loop
	while true; do
		# Read user input
		chunk_content=""
		blank_line_count=0
		while IFS= read -r -t "$timeout" line || [ -n "$line" ]; do
			if [ -z "$line" ]; then
				((blank_line_count++))
				if [ $blank_line_count -eq 2 ]; then
					break
				fi
			else
				blank_line_count=0
			fi
			chunk_content+="$line"$'\n'
		done

		# Check for EOF or timeout
		if [ -z "$chunk_content" ]; then
			break
		fi

		# Process the chunk
		((chunk_count++))
		process_chunk "$chunk_count" "$chunk_content" "$chat_log" "$summary_log" "$total_summary" "$model" "$plan_file"

		# Update plan if exists
		if [ -n "$plan_file" ]; then
			update_plan "$plan_file" "$summary_log" "$model"
		fi
	done

	# Summarize the current session
	summarize_session "$summary_log" "$total_summary" "$model"

	# restore caller options
	eval "$old_opts"
}

process_chunk() {
	local chunk_num=$1
	local content=$2
	local chat_log=$3
	local summary_log=$4
	local total_summary=$5
	local model=$6
	local plan_file=$7

	# Append chunk to chat log
	{
		echo "Chunk $chunk_num:"
		echo "$content"
		echo
		echo
	} >> "$chat_log"

	# Generate AI response
	local context=$(cat "$summary_log" "$total_summary")
	local plan=""
	[ -n "$plan_file" ] && plan=$(cat "$plan_file")

	local ai_response=$(query -m="$model" \
		"Context: $context" \
		"Plan: $plan" \
		"User input: $content" \
		"Please respond to the user's input, considering the context and plan.")

	# Append AI response to chat log
	{
		echo "AI Response:"
		echo "$ai_response"
		echo
		echo
	} >> "$chat_log"

	# Summarize the chunk
	local chunk_summary=$(query -m="$model" \
		"Please summarize the following conversation chunk:" \
		"$(tail -n +$((2 * chunk_num - 1)) "$chat_log" | head -n 4)")

	# Append chunk summary to summary log
	echo "$chunk_summary" >> "$summary_log"
	echo >> "$summary_log"
	echo >> "$summary_log"
}

update_plan() {
	local plan_file=$1
	local summary_log=$2
	local model=$3

	local updated_plan=$(combo -m="$model" "$plan_file" "$summary_log" \
		"Please update the interview plan based on the current summary. "\
		"Add new topics or questions if needed, and remove completed ones.")

	echo "$updated_plan" > "$plan_file"
}

summarize_session() {
	local summary_log=$1
	local total_summary=$2
	local model=$3

	local session_summary=$(query -m="$model" \
		"Please provide a comprehensive summary of the entire interview session:" \
		"$(cat "$summary_log")")

	# Append session summary to total summary
	{
		echo "Session Summary ($(date)):"
		echo "$session_summary"
		echo
		echo
	} >> "$total_summary"

	# Generate total summary of all sessions
	local new_total_summary=$(query -m="$model" \
		"Please provide an overall summary of all interview sessions:" \
		"$(cat "$total_summary")")

	echo "$new_total_summary" > "$total_summary"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	interview "$@"
fi

# version: 0.1.0

# Here's the `interview.sh` script based on your requirements and in the style of `hello_sh.sh`:

# This script implements the requested functionality for `interview.sh`, following the style and conventions of `hello_sh.sh`. It includes the main interview loop, chunk processing, summarization, and plan updating features. The script uses the specified tools (`process`, `summary`, `combo`) and follows the guidelines for error handling, option processing, and overall structure.

