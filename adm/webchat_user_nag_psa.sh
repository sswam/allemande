#!/bin/bash -eu
nag_file="$(realpath "$1")"
cd "$ALLEMANDE_USERS"
find . -maxdepth 1 -type d | while read user_dir; do
	cp -a "$nag_file" "$user_dir/nag.html"
done
