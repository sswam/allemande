#!/bin/bash

# [commits]
# Shows all commits in the git log history, from start to finish

git_show_all() {
	local r=  # repository path
	local n=  # limit number of commits to show
	local f=  # format for git show

	. opts

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	# Change to the specified repository directory if provided
	if [ -n "$r" ]; then
		cd "$r"
	fi

	# Get all commit hashes in reverse order
	local commits
	if [ -n "$n" ]; then
		commits=$(git log --reverse --format="%H" -n "$n")
	else
		commits=$(git log --reverse --format="%H")
	fi

	# color?
	color=
	if [ -t 1 ]; then
		color="--color=always"
	fi

	# Show each commit
	while read -r commit; do
		if [ -n "$f" ]; then
			git show --format="$f" $color "$commit"
		else
			git show $color "$commit"
		fi
		echo "----------------------------------------"
	done <<< "$commits" | less -R

	# restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	git_show_all "$@"
fi
