#!/usr/bin/env bash
# [user's name]
# Flatten a tree of files by renaming and moving to current dir, replacing / with sep

# shellcheck disable=SC1007,SC2034  # Disable certain shellcheck rules that conflict with ally options parser syntax

flatten_tree() {
	local sep= s="__"  # separator to replace / in filenames

	eval "$(ally)"

	while IFS= read -r file; do
		if [ -z "$file" ]; then continue; fi
		if ! [ -f "$file" ]; then
			printf >&2 "Not a file: %s\n" "$file"
			continue
		fi
		normalized=$(normalize "$file")
		target="${normalized//\//$sep}"
		dirname=$(dirname "$file")
		if mv "$file" "$target"; then
			if [[ $dirname != . ]] && [[ $dirname != .. ]] && [[ $dirname != /* ]] && [[ $dirname != */..* ]]; then
				rmdir -p "$dirname" 2>/dev/null || true
			fi
		else
			printf >&2 "Failed to move %s to %s\n" "$file" "$target"
		fi
	done
}

normalize() {
	local path="$1"
	while [[ $path == ./* ]] || [[ $path == ../* ]]; do
		if [[ $path == ./* ]]; then
			path=${path#./}
		elif [[ $path == ../* ]]; then
			path=${path#../}
		fi
	done
	printf '%s\n' "$path"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	flatten_tree "$@"
fi

# version: 0.1.0
