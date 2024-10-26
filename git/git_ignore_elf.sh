#!/usr/bin/env bash

# [files...]
# Updates .gitignore with ELF files in the git repository

git-ignore-elf() {
	local file=.gitignore
	local verbose= v=

	eval "$(ally)"

	cd "$(git-root)" || die "Not in a git repository"

	local new="$file.new.$$"

	{
		if [ -e "$file" ]; then
			cat "$file"
		fi
		find-elf . | grep -v '/\.' | sed 's,^./,/,'
	} | uniqo >"$new"

	if [ "$verbose" = 1 ]; then
		printf >&2 "Updating %s\n" "$file"
	fi

	mv "$new" "$file"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	git-ignore-elf "$@"
fi

# version: 0.1.0
