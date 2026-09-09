#!/bin/bash
# [-e] username*
# View or edit web user info.rec files

edit= e= # edit rather than view

eval "$(ally)"

for user; do
	file="$ALLEMANDE_USERS/$user/info.rec"
	if [ -n "$edit" ]; then
		vim "$file"
	else
		cat "$file"
	fi
done
