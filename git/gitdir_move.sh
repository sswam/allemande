#!/usr/bin/env bash
# Move a Git repository's .git directory to a new location, and update the original .git to a file that points to the new location.
# source dest
src=$1; dst=$2; [ -d "$src/.git" ] && src=$src/.git
mv -T -- "$src" "$dst"
printf 'gitdir: %s\n' "$dst" > "$src"
