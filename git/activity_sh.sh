#!/bin/bash

# [number of days]
# Shows git commit activity per day for the last n days

activity() {
	local days= d=7               # number of days to show, default 7
	local repo_path= r=           # path to git repository
	local format= f="short"       # output format [short|long]
	local count_loc= l=           # count lines of code
	local count_added_changed= a= # count only added/changed lines

	. opts # Note to AI: This magically loads options into the above vars

	# strict mode
	local old_opts=$(set +o)
	set -e -u -o pipefail

	# Note to AI: The following supports the short options above
	days=${days:-$d}
	repo_path=${repo_path:-$r}
	format=${format:-$f}
	count_loc=${count_loc:-$l}
	count_added_changed=${count_added_changed:-$a}

	# Validate inputs
	if [ -z "$days" ] || ! [[ "$days" =~ ^[0-9]+$ ]]; then
		echo >&2 "Error: Invalid number of days: $days"
		return 1
	fi

	# Change to the repository directory if specified
	if [ -n "$repo_path" ]; then
		if [ ! -d "$repo_path" ]; then
			echo >&2 "Error: Repository path does not exist: $repo_path"
			return 1
		fi
		cd "$repo_path"
	fi

	# Check if current directory is a git repository
	if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
		echo >&2 "Error: Not a git repository"
		return 1
	fi

	# Get commit activity
	local activity
	activity=$(git log --all --format="%cd" --date=short | sort -u | tail -n "$days" |
		while read -r date; do
			count=$(git log --all --format="%cd" --date=short --before="$date 23:59:59" --after="$date 00:00:00" | wc -l)
			loc=""
			added_changed=""
			if [ "$count_loc" = 1 ]; then
				loc=$(git log --all --before="$date 23:59:59" --after="$date 00:00:00" --numstat | awk '{if ($1 ~ /^[0-9]+$/ && $2 ~ /^[0-9]+$/) {added+=$1; removed+=$2}} END {print (added+removed > 999999 ? "999999+" : added+removed)}')
			fi
			if [ "$count_added_changed" = 1 ]; then
				added_changed=$(git log --all --before="$date 23:59:59" --after="$date 00:00:00" --numstat | awk '{if ($1 ~ /^[0-9]+$/) {added+=$1}} END {print (added > 999999 ? "999999+" : added)}')
			fi
			echo "$date $count $loc $added_changed"
		done)

	# Display activity based on format
	if [ "$format" = "long" ]; then
		echo "Commit activity for the last $days days:"
		echo "$activity" | while read -r date count loc added_changed; do
			output="$date: $count commit(s)"
			[ -n "$loc" ] && output="$output, $loc lines of code"
			[ -n "$added_changed" ] && output="$output, $added_changed added/changed lines"
			echo "$output"
		done
	else
		headers="Date Commits"
		[ "$count_loc" = 1 ] && headers="$headers LOC"
		[ "$count_added_changed" = 1 ] && headers="$headers Added/Changed"
		echo "$headers"
		echo "$activity" | column -t
	fi

	# restore caller options
	eval "$old_opts"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	activity "$@"
fi

# version: 0.1.3

# I understand your concern about the wild numbers in the output. Let's improve the `activity.sh` script to address this issue. Here's an updated version:

# Changes made:
#
# 1. Bumped the patch version from 0.1.2 to 0.1.3.
# 2. Modified the awk commands in the git log section to handle invalid input and cap large numbers:
# - Added checks to ensure we're only processing numeric values for added and removed lines.
# - Capped the maximum value for LOC and added/changed lines to 999999+.
# 3. Updated the condition for displaying headers in the short format to check if the value is 1 instead of "true".
#
# These changes should prevent the script from outputting extremely large numbers and improve its robustness when dealing with potentially invalid input from git log. The cap of 999999+ provides a reasonable upper limit for display purposes while still indicating when the actual number exceeds this value.
