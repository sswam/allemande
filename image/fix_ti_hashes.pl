#!/usr/bin/perl -p
# When A1111 comments in generated images, it can repeat textual inversion hashes many times.
# This script deduplicats them. Maybe I should just fix the bug...!
s/(TI hashes: ")(.*?)"/$1.join(", ", keys %{{map {$_ => 1} split(", ", $2)}}).'"'/e;
