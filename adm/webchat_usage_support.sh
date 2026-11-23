#!/bin/bash
# show users with high usage, and their level of support
threshold="${1:-2.5}"
year_month="${2:-$(date +%Y-%m)}"
file="$HOME/users-high-$year_month.txt"
webchat-usage-top "$year_month" |
awk '$2 >= '"$threshold" |
(IFS=$'\t'; while read user usage; do
	support=$(wui "$user" | grep '^support:' | kut 2)
	techo "$user" "$usage" "$support"
done) | tee "$file"
if [ -t 1 ]; then
	vi "$file"
fi
