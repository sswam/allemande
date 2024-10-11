#!/bin/bash -eu
# [dir ...]
# find dead symlinks
eval "$(ally)"
find "$@" -type l |
while read L; do
	[ -L "$L" ] && [ ! -e "$L" ] && echo "$L"
done
