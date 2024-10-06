#!/usr/bin/perl -w

use strict;
use Getopt::Std;
use vars qw/$opt_d/;

getopts("d");

my %hash = map {$_-1, 1} @ARGV;
my @F;
my @last;

while (defined ($_=<STDIN>)) {
	chomp;
	@F = split /\t/, $_, -1;

	my $i = 0;
	for (@F) {
		print "\t" if $i;
		print((%hash && !$hash{$i} or $_ ne ($last[$i]||'')) ?
			$_ :
			$opt_d && $_ ne "" ?
				"." :
				"");
		++$i;
	}
	print "\n";
	@last = @F;
}
