#!/bin/bash -eu
# vi_user.sh:	
cd "$ALLEMANDE_USERS"
files=()
for name; do
	files+=("$name/info.rec")
done
vi -O "${files[@]}"
