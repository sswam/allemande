#!/bin/bash
cd "$ALLEMANDE_USERS"
for user; do
	vi -O "$user/nag.html" "$user/nag.html.old" "$user/info.rec" ~/nag.html
done
