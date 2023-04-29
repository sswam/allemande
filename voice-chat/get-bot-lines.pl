#!/usr/bin/perl -n
# Get the lines spoken by the bot from the chat.

use strict;
use warnings;
chomp;
our $last;
BEGIN {
	$|=1;
	$last = "user";
}
if (/^$/) {
	warn "blank line\n";
	$last = "";
} elsif (/^\Q$ENV{user}\E:/) {
	warn "user line: $_\n";
	$last = "user";
} elsif (/^\Q$ENV{bot}\E:/ || (!/^\w+:/) && $last eq "bot") {
	warn "bot line: $_\n";
	$last = "bot";
	s/^\Q$ENV{bot}\E:\s*//;
	print("$_\n");
} else {
	warn "skipping line: $_\n";
}
