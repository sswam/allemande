#!/usr/bin/perl -w
# kut: keep only the specified columns

use strict;
use List::Util qw(max);
use vars qw($opt_w);	# -w: warn on missing columns
use vars qw(@slice);	# columns to keep, numbered from 1

our $max_slice;

use Getopt::Std;

# TODO add -q option
sub main {
	my $line;
	while (defined ($line = <STDIN>)) {
		chomp $line;
		my @row = split /\t/, $line, -1;
		if (!$opt_w) {
			# add empty columns
			my $add = $max_slice - @row;
			push @row, ('') x $add if $add > 0;
		}
		@row = @row[@slice];
		@row = map { !defined $_ ? '' : $_ } @row;
		print join "\t", @row;
		print "\n";
	}
}

sub get_args {
	getopts('w');
	@slice = @ARGV;
	@slice = map { $_ - 1 } @slice;
	$max_slice = max @slice;
}

if (!caller) {
	get_args();
	main();
}
