#!/bin/bash -eu
# cat_user.sh:	
cd "$ALLEMANDE_USERS"
files=()
for name; do
	files+=("$name/info.rec")
done
catpg "${files[@]}"
