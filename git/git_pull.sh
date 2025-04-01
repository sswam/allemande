#!/bin/sh -e
cd "`git-root`"
git pull --rebase "$@"
git status
