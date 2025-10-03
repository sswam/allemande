#!/usr/bin/env bash

# [-r|--remove] [-t|--time]
# Adds or removes profiling marks to/from bash scripts

add_mark() {
	if [ "$is_top_level" = 1 ] && [ -z "$line" ] && [ -n "$prev_line" ]; then
		if [ "$time" = 1 ]; then
			echo ': ${bash_mark_time:=${EPOCHREALTIME/.}}; echo >&2 "# mark '$mark_num' $(( (${EPOCHREALTIME/.}-bash_mark_time)/1000 ))"'
		else
			echo "echo >&2 \"# mark $mark_num\""
		fi
		((mark_num++))
	fi
}

bash-mark() {
	local remove= r=     # remove marks instead of adding them
	local time= t=       # add timestamps to marks

	eval "$(ally)"

	local mark_num=1
	local line
	local prev_line=""
	local is_top_level=1

	while IFS= read -r line; do
		if [ "$remove" = 1 ]; then
			if [[ ! "$line" =~ 'echo >&2 "# mark' ]]; then
				printf '%s\n' "$line"
			fi
			continue
		fi

		# Check if we're at top level
		if [[ "$line" =~ ^[[:space:]] || "$line" =~ ^[}\)] ]]; then
			is_top_level=0
		else
			is_top_level=1
		fi

		# Add mark if needed
		add_mark

		printf '%s\n' "$line"
		prev_line=$line
	done

	# Add final mark if last line wasn't empty
	line=""
	add_mark
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	bash-mark "$@"
fi
