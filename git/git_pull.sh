#!/bin/bash -e

cd "$(git-root)"

stash=0
if [ "$1" = "-s" ]; then
	stash=1
	shift
fi

if (( stash )); then
	git stash
fi

git pull --rebase "$@"

if (( stash )); then
	git stash pop
fi

git status
