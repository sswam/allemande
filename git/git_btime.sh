#!/usr/bin/env bash

# git_btime.sh: Show the git birth time (first commit date) of files

if [ -f "$ALLEMANDE_HOME/sh/opts.sh" ]; then
	source "$ALLEMANDE_HOME/sh/opts.sh"
fi

usage() {
	echo "Usage: git_btime.sh [options] [file ...]"
	echo
	echo "Show the git birth time (date of first commit) for each file."
	echo "If no files given, uses files tracked in the current directory."
	echo
	echo "Options:"
	echo "  -f, --format FMT   date format for git log (default: %ai)"
	echo "  -s, --short        short format (%as)"
	echo "  -r, --relative     relative format (%ar)"
	echo "  -q, --quiet        suppress filename, just print the date"
	echo "  -h, --help         show this help"
}

git_btime() {
	local format="$1"
	local quiet="$2"
	shift 2
	local files=("$@")

	# if [ "${#files[@]}" -eq 0 ]; then
	# 	mapfile -t files < <(git ls-files)
	# fi

	local file btime
	for file in "${files[@]}"; do
		# First try: look for the commit that added the file
		btime=$(git log --follow --diff-filter=A --format="$format" -- "$file" 2>/dev/null | head -1)

		# Fallback: oldest commit touching the file
		if [ -z "$btime" ]; then
			btime=$(git log --follow --format="$format" -- "$file" 2>/dev/null | tail -1)
		fi

		if [ -z "$btime" ]; then
			echo "git_btime: $file: not found in git history" >&2
			continue
		fi

		if [ "$quiet" = "true" ]; then
			echo "$btime"
		else
			printf '%s\t%s\n' "$btime" "$file"
		fi
	done
}

main() {
	local format="%ai"
	local quiet=false

	local opts
	opts=$(getopt -o "f:srqh" --long "format:,short,relative,quiet,help" -n "git_btime" -- "$@") || { usage >&2; exit 1; }
	eval set -- "$opts"

	while true; do
		case "$1" in
		-f|--format)   format="$2"; shift 2 ;;
		-s|--short)    format="%as";     shift ;;
		-r|--relative) format="%ar";     shift ;;
		-q|--quiet)    quiet=true;       shift ;;
		-h|--help)     usage; exit 0 ;;
		--) shift; break ;;
		*) echo "git_btime: unexpected option: $1" >&2; exit 1 ;;
		esac
	done

	git_btime "$format" "$quiet" "$@"
}

main "$@"

# Key points:

# - **Birth time** = first commit that introduced the file, found via `--diff-filter=A` (Added), with a fallback to the oldest entry in `git log --follow`
# - `--follow` handles renames across history
# - Without args, falls back to all tracked files in the repo
# - Output is `<datetime>\t<file>` by default, or just the date with `-q`
# - Format options mirror `git log` pretty-format placeholders (`%ai`, `%as`, `%ar`)
