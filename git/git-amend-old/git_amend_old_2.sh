#!/bin/bash

# Amends a previous commit using interactive rebase

set -e -u

commit=$1
message=$2
parent=$(git rev-parse "$commit"^)

stashed=0  # Initialize stashed to prevent unset variable error

if ! git diff --staged --quiet; then
	git stash push -m "temp-amend-stash"
	stashed=1
fi

GIT_SEQUENCE_EDITOR="sed -i '$,/pick/s/pick/edit/'" git rebase -i "$parent"

if [ "$stashed" = 1 ]; then
	if ! git stash pop; then
		echo "Conflicts detected. Fix them and run 'git rebase --continue'" >&2
		${SHELL:-/bin/bash}
		exit 1
	fi
fi

if [ -n "$message" ]; then
	git commit --amend -m "$message"
else
	git commit --amend
fi

git rebase --continue
