#!/usr/bin/env bash

# logs [number|program]
# Displays the specified log file or a recent log file in less
# Usage:
#   logs            - Display the most recent log file
#   logs 3          - Display the 3rd most recent log file
#   logs program    - Display the log file for 'program'
#   logs -l         - List all log files
# Version: 1.0.1

logs() {
	local list= l=  # Variables for listing all log files

	eval "$(ally)"

	local arg=${1:-}

	local log_dir="$HOME/.logs"

	# If list option is set, display all log files
	if [ "$list" = 1 ]; then
		ls -tcr "$log_dir"/*.log | less -G
		return
	fi

	local number=1
	local prog=

	# Determine if argument is a number or program name
	if [[ $arg =~ ^[0-9]+$ ]]; then
		number=$arg
	else
		prog=$arg
	fi

	local log_file

	# Set log file based on input
	if [ -n "$prog" ]; then
		log_file="$log_dir/$prog.log"
		# glob if not exists
		if [ ! -f "$log_file" ]; then
			log_file=$(
				ls -tcr "$log_dir/$prog"*.log 2>/dev/null |
				head -n 1
			)
		fi
	else
		# Get nth most recent log file
		log_file=$(
			ls -tcr "$log_dir"/*.log 2>/dev/null |
			grep -v opts-long |
			tail -n "$number" | head -n 1
		)
	fi

	# Check if log file exists
	if [ ! -f "$log_file" ]; then
		echo >&2 "Log file not found"
		return 1
	fi

	# Display log file using less
	less +G "$log_file"
}

# Run the function if script is executed directly
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	logs "$@"
fi

