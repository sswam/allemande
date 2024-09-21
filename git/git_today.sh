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

	# need to subtracte one day to include today
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

# Here's the `git_today.sh` script written in the style of `hello.sh`:

# This script follows the structure and style of `hello.sh` while implementing the requested functionality. Here's a breakdown of the features:
#
# 1. It uses the same header format and strict mode setup.
# 2. The script can process multiple repositories or the current repository if none are specified.
# 3. It includes options for:
# - Different start date (`d`)
# - Filtering by user (`u`)
# - Showing the patch with each log entry (`p`)
# 4. It uses the `. opts` call to handle options and usage automatically.
# 5. The script checks if each specified path is a git repository before processing.
# 6. It constructs the git command based on the provided options.
# 7. The script can be used as a CLI tool or as a bash library.
#
# To use this script, you would typically call it like this:

# ./git_today.sh -d 2023-05-01 -u "John Doe" -p -r /path/to/repo1 -r /path/to/repo2

# This would show git logs since May 1, 2023, for the user "John Doe", including patches, for the specified repositories.
