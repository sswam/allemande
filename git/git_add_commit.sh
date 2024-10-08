#!/bin/bash -eu
set -o pipefail

if [ -n "`git-ls-untracked`" -o -n "`git-ls-unstaged`" ]; then
	git status
	confirm git add -A || true
	echo
fi

if [ -n "`git-ls-staged`" ]; then
	git status
	messy
#	GIT_EDITOR='nvim -c startinsert' confirm git commit || true
	echo
fi
