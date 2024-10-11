#!/usr/bin/env bash
# [file ...]
# find the full path of a command or file in PATH

eval "$(ally)"

ALL=
for O in "${OPTS[@]}"; do
	case O in
	-a|--all) ALL=1 ;;
	*) . usage [-a] filename ...
	esac
done

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
			[ -n "$ALL" ] || break
		fi
	done
	if [ -z "$found" ]; then
		not_in_path
	fi
done
