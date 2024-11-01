#!/usr/bin/perl
use HTML::Entities;
while (<STDIN>) {
	for my $i (0..$#ARGV) {
		my $attr = $ARGV[$i];
		if ($i > 0) {
			print "\t";
		}
		if (/ $attr="(.*?)"| $attr='(.*?)'| $attr=(.*?)[ >]/i) {
			print decode_entities(defined $1 ? $1 : defined $2 ? $2 : $3);
		}
	}
	print "\n";
}
