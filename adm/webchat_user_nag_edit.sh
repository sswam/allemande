#!/bin/bash
for user; do
	vi -O "$ALLEMANDE_USERS/$user/nag.html" "$ALLEMANDE_USERS/$user/nag.html.old" "$ALLEMANDE_USERS/$user/info.rec"
done
