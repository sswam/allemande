#!/usr/bin/env bash

# Amends a previous commit using interactive rebase

git-amend-old() {
	dry_run= d=      # show what would be done without doing it
	editor= e=       # editor to use for rebase
	message= m=      # new commit message

	eval "$(ally)"

	[ $# -eq 1 ] || usage

	commit=$1

	if [ "$dry_run" = 1 ]; then
		printf >&2 "Would rebase interactively to %s\n" "${commit}"
		return 0
	fi

	# Check if we're in a git repository
	if ! git rev-parse --git-dir >/dev/null 2>&1; then
		die "not a git repository"
	fi

	# Check if there are uncommitted changes
	if ! git diff-index --quiet HEAD --; then
		die "uncommitted changes present, please commit or stash them first"
	fi

	# Set editor if specified
	if [ -n "$editor" ]; then
		export GIT_EDITOR="$editor"
	fi

	# Prepare rebase command with either commit hash or relative reference
	if ! [[ "$commit" =~ ^[0-9a-f]{4,}$ ]]; then
		commit="HEAD~${commit}"
	fi
	rebase_cmd=(git rebase -i "$commit")

	# Start interactive rebase
	if ! "${rebase_cmd[@]}" </dev/tty; then
		die "rebase failed"
	fi

	# If a new message was provided, use it during the amend
	if [ -n "$message" ]; then
		if ! git commit --amend -m "$message"; then
			die "commit amend failed"
		fi
	else
		if ! git commit --amend; then
			die "commit amend failed"
		fi
	fi

	# Continue the rebase
	if ! git rebase --continue; then
		die "rebase continue failed"
	fi

	printf "Successfully amended the commit\n"
}

if [ "${BASH_SOURCE[0]}" = "$0" ]; then
	git-amend-old "$@"
fi

# version: 0.1.2

# TODO not sure if this works yet... it doesn't seem to destroy things though, so that's good
