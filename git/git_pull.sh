#!/bin/bash -e

cd "$(git-root)"

stash=0
if [ "$1" = "-s" ]; then
	stash=1
	shift
fi

if (( stash )); then
	if git diff-index --quiet HEAD --; then
		stash=0
	else
		git stash push -m "pull-tmp-$$"
	fi
fi

git pull --rebase "$@"

if (( stash )); then
	git stash pop "$(git stash list | grep "pull-tmp-$$" | cut -d: -f1)"
fi

git status
