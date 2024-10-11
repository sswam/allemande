#!/usr/bin/env bash

# [files...]
# Make files executable if they start with a valid shebang

chmod-x-shebang() {
	local verbose= v=	# print more information
	local quiet= q=		# print less information

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

			if [ "$interpreter" = "/usr/bin/env" ] || [ "$interpreter" = "/bin/env " ]; then
				if [ -x "$interpreter" ]; then
					interpreter=${first_line#* }
					interpreter=${interpreter%% *}
					interpreter=$(which "$interpreter")
				fi
			fi

			if [ "$quiet" != 1 ]; then
				if [ ! -f "$interpreter" ]; then
					echo >&2 "Interpreter not found: $first_line"
				elif [ ! -r "$interpreter" ]; then
					echo >&2 "Interpreter not readable: $first_line"
				elif [ ! -x "$interpreter" ]; then
					echo >&2 "Interpreter not executable: $first_line"
				fi
			fi
		else
			mode="-x"
		fi

		# Check if the mode is already correct
		if [ -x "$file" ]; then
			if [ "$mode" = "+x" ]; then
				mode=""
			fi
		else
			if [ "$mode" = "-x" ]; then
				mode=""
			fi
		fi

		if [ -n "$mode" ]; then
			chmod "$mode" "$file"
		fi

		case "$mode" in
		"+x") char="x" ;;
		"-x") char="-" ;;
		"") char=" " ;;
		esac


		if [ "$quiet" != 1 ]; then
			if [ "$verbose" = 1 ] || [ -n "$mode" ]; then
				printf "%s %s\n" "$char" "$file"
			fi
		fi
	done
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	chmod-x-shebang "$@"
fi
