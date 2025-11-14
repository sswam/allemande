#!/usr/bin/bash
# audit webchat users based on messages in the last 30 days
# outputs audit.tsv and updates info.rec files
#
set -e -u

cd "$ALLEMANDE_ROOMS"
find . -name '*.bb' -mtime -30 -printf '%P\n'
while read -r file; do
	room=${file%.bb}
	mtime=$(stat -c %y "$file")
	mtime=${mtime%.*}
#	< "$file" grep -oP '^\p{Lu}\p{Ll}+(?=:\t)' | prepend "$mtime	$room	"
	< "$file" grep -oP '^[^ ]+(?=:\t)' | prepend "$mtime	$room	"
done |
awk -F'\t' '
	{
		count[$3]++
		# Check if room is public, private, nsfw, sfw, ...
		if ($2 ~ /^nsfw\//) {
			public[$3]++
			nsfw[$3]++
		} else if ($2 ~ /^sanctuary\//) {
			public[$3]++
			nsfw[$3]++
		} else if ($2 ~ /\//) {
			private[$3]++
		} else {
			public[$3]++
			sfw[$3]++
		}
		if (!seen[$3] || $1 > times[$3] || ($1 == times[$3] && $2 < rooms[$3])) {
			times[$3] = $1
			rooms[$3] = $2
			seen[$3] = 1
		}
	}
	END {
		for (user in seen) {
			priv = (private[user] ? private[user] : 0)
			pub = (public[user] ? public[user] : 0)
			nsfw = (nsfw[user] ? nsfw[user] : 0)
			sfw = (sfw[user] ? sfw[user] : 0)
			print tolower(user) "\t" times[user] "\t" rooms[user] "\t" count[user] "\t" priv "\t" pub "\t" sfw "\t" nsfw
		}
	}
' | order 1 > ~/audit.tsv

(
	IFS=$'\t'
	while read -r user mtime room count private public sfw nsfw; do
		info="$ALLEMANDE_USERS/$user/info.rec"
		[ -e "$info" ] || continue
		sed -i '/^\(mtime\|room\|count\|private\|public\|sfw\|nsfw\):/d; /^$/d;' "$info"
		(
			techo mtime room count private public sfw nsfw
			techo "$mtime" "$room" "$count" "$private" "$public" "$sfw" "$nsfw"
		) | tsv2recs -a >> "$info"
	done
) < ~/audit.tsv

cd "$ALLEMANDE_USERS"

# shellcheck disable=SC2035
jf ~/users.rec */info.rec

# version: 0.0.2
