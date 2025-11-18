#!/usr/bin/env bash

# [file ...]
# Force add and commit files, regardless of git status

# shellcheck disable=SC1007,SC2034

git-commit-force() {
	local message= m="chore: auto-commit"  # commit message
	local add= a=                          # only add files, don't commit

	eval "$(ally)"

	status=0
	quiet=
	if [ "$log_level" -ge 3 ]; then
		quiet="-q"
	fi

	for file; do
		local dir
		local basename
		dir=$(dirname "$file")
		basename=$(basename "$file")

		# Check if file has unadded changes
		local has_unadded=
		if (
			cd "$dir"
			git status --porcelain "$basename" | grep -q '^??'
		); then
			has_unadded=1
		fi

		# Check if file has uncommitted changes
		local has_uncommitted=
		if (
			cd "$dir"
			git status --porcelain "$basename" | grep -q '^[MADRCU]'
		); then
			has_uncommitted=1
		fi

		# No changes, skip this file
		if [ "$has_unadded" != 1 ] && [ "$has_uncommitted" != 1 ]; then
			continue
		fi

		# Process in subshell to isolate directory changes
		if ! (
			cd "$dir"

			# Force add the file if it has unadded changes
			if [ "$has_unadded" = 1 ]; then
				git add -f "$basename" || exit 1
			fi

			# Add if it has uncommitted changes
			if [ "$has_uncommitted" = 1 ]; then
				git add "$basename" || exit 1
			fi

			# Commit if not in add-only mode
			if [ "$add" != 1 ]; then
				git commit $quiet -m "$message" -- "$basename" || exit 1
			fi
		); then
			status=1
		fi
	done

	return "$status"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	git-commit-force "$@"
fi

# version: 0.1.2
