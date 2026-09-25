#!/bin/bash
# show users with high usage, and their level of support
threshold="${1:-2.5}"
webchat-usage-top |
awk '$2 >= '"$threshold" |
(IFS=$'\t'; while read user usage; do
	support=$(wui "$user" | grep '^support:' | kut 2)
	techo "$user" "$usage" "$support"
done) | tee ~/users-high.txt
if [ -t 1 ]; then
	vi ~/users-high.txt
fi
