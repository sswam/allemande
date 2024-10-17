#!/bin/bash

# [start_date] [user]
# Show all git logs from today for the listed repos (or current repo)

git_today() {
	local d=$(date +%Y-%m-%d)  # default to today
	local u=                   # user filter
	local p=0                  # show patch
	local color=auto           # colorize output

	. opts

	repos=( "$@" )

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	# need to subtract one day to include today
	d=$(date -d "$d -1 day" +%Y-%m-%d)

	# If no repos specified, use current repo
	if [ ${#repos[@]} -eq 0 ]; then
		repos=( . )
	fi

	if [ -t 1 -a "$color" = "auto" ]; then
		color=always
	fi

	for repo in "${repos[@]}"; do (
		cd "$repo"
		cd "$(git-root)"

		if [ ! -d ".git" ]; then
			echo >&2 "Warning: $PWD is not a git repository"
			exit
		fi

		echo "## Repository: $PWD"
		echo

		local git_cmd="git log --color=$color --since=$d"
		if [ -n "$u" ]; then
			git_cmd+=" --author=$u"
		fi
		if [ "$p" = 1 ]; then
			git_cmd+=" -p"
		fi

		$git_cmd || true

		echo
		echo
	) done | less -R

	# restore caller options
	eval "$old_opts"
}

if [ "$BASH_SOURCE" = "$0" ]; then
	git_today "$@"
fi
