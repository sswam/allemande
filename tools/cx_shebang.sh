#!/usr/bin/env bash

# [files...]
# Make files executable if they start with a valid shebang

cx_shebang() {
	local verbose= v=	# print more information

	eval "$(ally)"

	local file
	for file in "$@"; do
		if [ ! -f "$file" ]; then
			echo >&2 "Skipping non-file: $file"
			continue
		fi

		local first_line
		first_line=$(head -n 1 < "$file")

		if [[ "$first_line" =~ ^#! ]]; then
			mode="+x"

			local interpreter
			interpreter=${first_line#\#!}
			interpreter=${interpreter%% *}

			if [ ! -f "$interpreter" ]; then
				echo >&2 "Warning: Interpreter not found: $interpreter"
			elif [ ! -r "$interpreter" ]; then
				echo >&2 "Warning: Interpreter not readable: $interpreter"
			elif [ ! -x "$interpreter" ]; then
				echo >&2 "Warning: Interpreter not executable: $interpreter"
			fi
		else
			mode="-x"
		fi

		# Check if the mode is already correct
		if [ -x "$file" ]; then
			if [ "$mode" = "+x" ]; then
				mode="  "
			fi
		else
			if [ "$mode" = "-x" ]; then
				mode="  "
			fi
		fi

		if [ "$mode" != "  " ]; then
			chmod "$mode" "$file"
		fi
		if [ "$verbose" = 1 ]; then
 		       	echo >&2 "$mode"$'\t'"$file"
		fi
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	cx_shebang "$@"
fi
