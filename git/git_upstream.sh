#!/bin/sh -e
BRANCH=$1
if [ -n "$BRANCH" ]; then
	git for-each-ref --format='%(upstream:short)' "$(git rev-parse --symbolic-full-name "$BRANCH")"
else
	git for-each-ref --format='%(upstream:short)' "$(git symbolic-ref -q HEAD)"
fi
