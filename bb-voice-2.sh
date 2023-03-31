#!/bin/bash -eu
# bb-voice: a simple voice chat program

set -a

file="$1"
user="$2"
bot="$3"
add_prompts="${4:-}"
mission=${5:-"* $bot is $user's good friend."}

: ${SPEAK:=speak.sh -tempo=30 -pitch=1}

. opts

if [ ! -e "$file" ]; then
	> "$file"
fi

# rm -f /tmp/drop-the-mic

mike.py | tee /dev/stderr | (
while read line; do
	if [ ! -s "$file" -a -n "$mission" ]; then
		echo >&2 1
		printf "%s\n%s: %s\n" "$mission" "$user" "$line" >> "$file"
	elif [ -n "$add_prompts" ]; then
		echo >&2 2
		printf "%s: %s\n" "$user" "$line" >> "$file"
	else
		echo >&2 3
		printf "%s\n" "$line" >> "$file"
	fi
	while read -t 0.1 line; do
		:
	done || true
done 
) &

trap "pkill -P $$; rf -f /tmp/drop-the-mic" EXIT

#while true; do
	tail -f -n0 "$file" |
	perl -ne '
		BEGIN {
			$|=1;
			@speak = split / /, $ENV{SPEAK};
			$last = "user";
		}
		print STDERR "line: $_\n";
		s/[^ -~]//g; 
		print STDERR "line 2: $_\n";

		if ($. == 1) {
			# skip first line, that is the users message
			print STDERR "skipping first line: $_\n";
		} elsif (/^\Q$ENV{user}\E:/) {
			$last = "user";
		} elsif (/^\Q$ENV{bot}\E:/ || (!/^\w+: /) && $last eq "bot") {
			$last = "bot";
			print STDERR "$_\n";
			s/^\Q$ENV{bot}\E:\s*//;
#			system "touch", "/tmp/drop-the-mic";
			system "amixer", "sset", "Capture", "10%";
			system "v", @speak, " $_";
			system "amixer", "sset", "Capture", "100%";
#			system "rm", "-f", "/tmp/drop-the-mic";
#			exit(0);
		} else {
			print STDERR "skipping like with user or unknown role: $_\n";
		}
	'
#done
