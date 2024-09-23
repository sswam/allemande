#!/bin/bash -eu
# [command...] [-t seconds]
# Runs a command stealthily, erasing output after user input or time limit

. tty_cursor_pos_bash.sh

calculate_output_rows() {
	local text="${1%$'\n'}"
	local rows=0

	while IFS= read -r line; do
		local linewidth=${#line}
		local outrows=$(( (linewidth + COLUMNS - 1) / COLUMNS ))
		[ $outrows -le 0 ] && outrows=1
		rows=$(( rows + outrows ))
	done < <( printf '%s\n' "$text" | expand -t 8 | tr -dc '[:print:]\n' )

	echo "$rows"
}

stealthy() {
	local t= 	# time limit ("" means no limit)
	local i=	# interactive mode, for tools that interact with the user
	local c=	# check cursor positioning
	local a=	# wait for any key, not just enter (don't press arrows!)

	local status=0

	. opts

	if [ $# -eq 0 ]; then
		echo "Error: No command specified." >&2
		return 1
	fi

	# Run the command
	if [ "$i" = 1 ]; then
		# Save cursor position
		tput sc

		"$@"
	else
		# Check cursor positioning
		if [ "$c" = 1 ]; then
			tty_cursor_pos_bash -suffix=_before
		fi

		# Run the command and capture output
		output=$("$@" 2>&1)
		echo -n "$output"
		local rows=$(calculate_output_rows "$output")
	fi

	trap 'tput cvvis' EXIT

	# hide the cursor
	tput civis

	# read options
	read_opts="-s -r"
	if [ -n "$a" ]; then
		read_opts="$read_opts -n 1"
	fi
	if [ -n "$t" ]; then
		read_opts="$read_opts -t $t"
	fi

	# Wait for user input or time limit
	read $read_opts || true

	# Restore cursor position
	if [ "$i" = 1 ]; then
		tput rc
	else
		# Move cursor to beginning of line
		tput cr

		# move up by $rows
		tput cuu $rows

		# Check cursor positioning
		if [ "$c" = 1 ]; then
			tty_cursor_pos_bash -suffix=_after
			row_target=$(( $row_before - 1 ))
			if [ $row_after -ne $row_target ] || [ $col_after -ne 1 ]; then
				echo >&2 "Error: Final cursor position does not match target position"
				echo >&2 "$row_after $col_after -> $row_target 1"
				status=1
			fi
		fi
	fi

	# Clear the terminal from here to the end
	tput ed

	# Show the cursor
	tput cvvis

	return $status
}

if [ "$0" = "$BASH_SOURCE" ]; then
	stealthy "$@"
fi


# tput cuu N - Move cursor up N lines (CUU: Cursor Up)
# tput ed - Clear from cursor to end of screen (ED: Erase Display)
# tput cr - Move cursor to beginning of line (CR: Carriage Return)
# tput cuu1 - Move cursor up 1 line (CUU: Cursor Up)
# tput el - Clear from cursor to end of line (EL: Erase Line)
# tput cvvis - Make the cursor visible (CVVIS: Cursor Visible)
# tput civis - Make the cursor invisible (CIVIS: Cursor Invisible)
# tput sc - Save cursor position (SC: Save Cursor)
# tput rc - Restore cursor position (RC: Restore Cursor)
# tput cup Y X - Move cursor to row Y, column X (CUP: Cursor Position)
# tput lines - Get the number of lines in the terminal
