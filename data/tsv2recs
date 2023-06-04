#!/usr/bin/perl -w
use strict;
use warnings;
use utf8;
use open ':utf8';
use Data::Dumper;
use Text::TSV;

our $__in;
our $__out;
$__in = \*STDIN;  binmode($__in, ":utf8");
$__out = \*STDOUT;  binmode($__out, ":utf8");
my $__csv_in = Text::TSV->new;
my $in_names = $__csv_in->getline($__in);

while (1) {
	my $__row_in = $__csv_in->getline($__in);
	if (!$__row_in) {
		$__csv_in->eof or die $__csv_in->error_diag();
		last;
	}
	for my $i (0..$#$__row_in) {
		my ($k, $v) = ($in_names->[$i], $__row_in->[$i]);
		chomp $v;
		$v =~ s/^/\t/m;
		print $__out "$k:$v\n";
	}
	print $__out "\n";
}
