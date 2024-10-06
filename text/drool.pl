#!/usr/bin/perl -w
# drool: copy values from columns down, in a tab-delimited file

use strict;

sub max {
	$_[0] > $_[1] ? $_[0] : $_[1];
}

my %hash = map {$_-1, 1} @ARGV;
my @F;
my @acc;

while (defined ($_=<STDIN>)) {
	chomp;
	@F = split /\t/, $_, -1;
	if (@acc > @F) { splice @acc, 0+@F; }

	for my $i (0..max($#acc, $#F)) {
		$acc[$i] = $F[$i] if
			%hash && !$hash{$i} or !defined $acc[$i] or $F[$i] ne "";
		++$i;
	}

	print join "\t", @acc;
	print "\n";
}

