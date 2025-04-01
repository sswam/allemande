#!/bin/sh -e
cd "`git-root`"
remote=${1:-`git remote get-url origin`}
branch=`git rev-parse --abbrev-ref HEAD`
git push "$remote"
if [ -z "`git-upstream`" ]; then
	git branch -u origin/$branch $branch
fi
