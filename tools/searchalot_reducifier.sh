#!/bin/bash -eu
# searchalot_reducifier:	run searchalot_filter and split up into separate files
# kingdoms:	tourism industry education
for kingdom; do
	time searchalot_filter results-$kingdom/* > $kingdom.txt
	< $kingdom.txt grep -e 'https://www.youtube.com' > $kingdom-youtube.txt
	< $kingdom.txt grep -e 'https://www.tripadvisor.com' > $kingdom-tripadvisor.txt
	< $kingdom.txt grep -v -e 'https://www.youtube.com' -e 'https://www.tripadvisor.com' | grep -e 'https*:'> $kingdom-web.txt
	< $kingdom.txt grep -v -e 'https://www.youtube.com' -e 'https://www.tripadvisor.com' -e 'https*:'> $kingdom-list.txt
	for cutoff in `seq 1 10`; do
		dir=$kingdom-$cutoff
		mkdir -p "$dir"
		for suffix in "" -youtube -tripadvisor -web -list; do
			in="$kingdom$suffix.txt"
			out="$dir/$kingdom$suffix.txt"
			awk "\$1 >= $cutoff" < "$in" >"$out"
		done
	done
done
./searchalot_eval | less
