#!/bin/bash -eu
# git tools to list files in various states

prepend() {
	# Prepend a string to each line of stdin.
	local prefix="$1"
	shift
	perl -pe "s/^/\Q$prefix\E/"
}

git-ls-repo() {
	# List all files in the repository.
	git ls-files
}

git-ls-commit() {
	# List files in the commit.
	git diff-tree --no-commit-id --name-only -r "${@:-HEAD}"
}

git-ls-staged() {
	# List files in the staging area.
	git diff --cached --name-only
}

git-ls-unstaged() {
	# List files in the working directory that are not staged.
	git diff --name-only
}

git-ls-untracked() {
	# List files in the working directory that are not tracked.
	git ls-files --others --exclude-standard
}

git-ls-pending() {
	# List files in the working directory that are not committed.
	git-ls-unstaged | prepend $'unstaged\t'
	git-ls-untracked | prepend $'untracked\t'
	git-ls-staged | prepend $'staged\t'
}

git-ls-all() {
	# List files in the repository, commit, and working directory.
	git-ls-repo | prepend $'repo\t'
	git-ls-commit | prepend $'commit\t'
	git-ls-pending
}

if [ "$0" = "$BASH_SOURCE" ]; then
	"`basename "$0"`" "$@"
fi
