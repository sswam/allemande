#!/usr/bin/bash
set -e -u

cd "$ALLEMANDE_ROOMS"
find . -name '*.bb' -printf '%P\n' |
while read file; do
	room=${file%.bb}
	mtime=$(stat -c %y "$file")
	mtime=${mtime%.*}
	< "$file" grep -oP '^\p{Lu}\p{Ll}+(?=:\t)' | prepend "$mtime	$room	"
done |
awk -F'\t' '
	{
		count[$3]++
		if (!seen[$3] || $1 > times[$3] || ($1 == times[$3] && $2 < rooms[$3])) {
			times[$3] = $1
			rooms[$3] = $2
			seen[$3] = 1
		}
	}
	END {
		for (user in seen) {
			print tolower(user) "\t" times[user] "\t" rooms[user] "\t" count[user]
		}
	}
' | order 1 > ~/audit.tsv

(
	IFS=$'\t'
	while read -r user mtime room count; do
		info="$ALLEMANDE_USERS/$user/info.rec"
		[ -e "$info" ] || continue
		sed -i '/^\(mtime\|room\|count\):/d; /^$/d;' "$info" 
		(
			techo mtime room count
			techo "$mtime" "$room" "$count"
		) | tsv2recs -a >> "$info"
	done
) < ~/audit.tsv

cd "$ALLEMANDE_USERS"
jf ~/users.rec */info.rec
