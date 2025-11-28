#!/usr/bin/env bash
# Replace a .git symlink to a gitdir with a file that points to that location.
# symlink
src=$1; dst=$(readlink -f -- "$src")
move-rubbish "$src"
printf 'gitdir: %s\n' "$dst" > "$src"
