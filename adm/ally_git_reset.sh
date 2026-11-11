#!/bin/bash -eu
# reset an ally-git git repo
for dir; do
	dir=${dir%/.git}
	dir=$(realpath "$dir")
	name="$(basename "$dir")"
	git_link="$dir/.git"
	if [ ! -L "$git_link" ]; then
		echo >&1 "Not a symlink: $git_link"
		continue
	fi
	git=$(readlink -m "$git_link")
	ally_git_dir="$ALLEMANDE_HOME/ally-git/$name"
	expect="$ally_git_dir/.git"
	if [ "$git" != "$expect" ]; then
		echo >&1 "Symlink target not as expected: $git_link"
		continue
	fi
	rm -rf "$git"
	(
		mkdir -p "$ally_git_dir"
		cd "$ally_git_dir"
		yes n | arcs -i
		cd "$dir"
		arcs
	)
done
