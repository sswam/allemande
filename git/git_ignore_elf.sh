#!/usr/bin/env bash

# [files...]
# Updates .gitignore with ELF files in the git repository

git-ignore-elf() {
	local verbose= v=

	eval "$(ally)"

	local root="$(git-root)"
	local cwd_relpath="$(realpath --relative-to="$root" .)"
	local file="$root/.gitignore"

	touch "$file"

	# Find all ELF files under the current directory,
	# and add them to the .gitignore file if they are not already present.
	# Using slurp to avoid the possibility of re-reading our own output.
	find-elf . | grep -v '/\.' | sed 's,^./,/,' | prepend "/$cwd_relpath" | sort |
	comm -23 - <(< "$file" slurp | sort) | tee -a "$file"

	if [ "$verbose" = 1 ]; then
		printf >&2 "Updating %s\n" "$file"
	fi
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	git-ignore-elf "$@"
fi

# version: 0.1.0
