#!/usr/bin/env bash
# [file ...]
# find the full path of a command or file in PATH

all= a=	# show all files in PATH, not only the first

eval "$(ally)"

not_in_path() {
	if [ -e "$F" -o -n "${CREATE:-}" ]; then
		echo "$F"
	fi
}

IFS=:
for F; do
	found=
	case "$F" in
	"" | "." | ".." | /* | ./* | ../*) not_in_path; continue ;;
	esac
	for P in $PATH; do
		f="$P/$F"
		if [ -f "$f" ]; then
			echo "$f"
			found=1
			[ -n "$all" ] || break
		fi
	done
	if [ -z "$found" ]; then
		not_in_path
	fi
done
