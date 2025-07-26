#!/bin/bash
# [dir ...]
# find dead symlinks
eval "$(ally)"
set +e +u
find "$@" -type l |
while read L; do
	[ -L "$L" ] && [ ! -e "$L" ] && echo "$L"
done
exit 0
