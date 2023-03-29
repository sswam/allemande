#!/bin/bash -eu
# bb-voice: a simple voice chat program

set -a

file="$1"
user="$2"
bot="$3"
mission=${4:-"* $bot is $user's good friend."}
speed=1.3

> "$file"

rm -f /tmp/drop-the-mic

mike.py | tee /dev/stderr | (
first=1
while read line; do
	if [ -n "$first" ]; then
		printf "%s\n%s: %s\n" "$mission" "$user" "$line" > "$file"
		first=
	else
		printf "%s\n" "$line" >> "$file"
	fi
	while read -t 0.1 line; do
		:
	done || true
done 
) &

trap "pkill -P $$; rf -f /tmp/drop-the-mic" EXIT

while true; do
	tail -f -n0 "$file" |
	perl -ne '
		BEGIN {$|=1;}
		s/[^ -~]//g; 
		if ($. == 1) {
			# skip first line, that is the users message
		} elsif (/^\Q$ENV{bot}\E:/ || !/^\w+: /) {
			print STDERR "$_\n";
			s/^\Q$ENV{bot}\E:\s*//;
#			system "touch", "/tmp/drop-the-mic";
			system "amixer", "sset", "Capture", "10%";
			system "speak", "-speed=$ENV{speed}", " $_";
			system "amixer", "sset", "Capture", "100%";
#			system "rm", "-f", "/tmp/drop-the-mic";
			exit(0);a
		}
	'
done
