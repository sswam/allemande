#!/usr/bin/perl -w

use strict;
use warnings;
use utf8;
use open ':utf8';
use Text::TSV;
use Getopt::Long;

# Process command line options
my $include_all = 0;
GetOptions(
	"all|a" => \$include_all,
) or die "Error in command line arguments\n";

# Setup input/output handles with proper UTF-8 encoding
our $__in;
our $__out;
$__in = \*STDIN;  binmode($__in, ":encoding(UTF-8)");
$__out = \*STDOUT;  binmode($__out, ":encoding(UTF-8)");

# Initialize TSV parser and get header row
my $__csv_in = Text::TSV->new;
my $in_names = $__csv_in->getline($__in);

# Process each row of the TSV file
while (1) {
	my $__row_in = $__csv_in->getline($__in);
	if (!$__row_in) {
		$__csv_in->eof or die $__csv_in->error_diag();
		last;
	}

	# Output fields according to include_all flag
	for my $i (0..$#$in_names) {
		my $k = $in_names->[$i];
		my $v = $__row_in->[$i];
		# Skip undefined values unless include_all is set
		next if !$include_all && !defined $v;
		$v //= '';
		chomp $v;
		$v =~ s/^/\t/m;
		print $__out "$k:$v\n";
	}

	print $__out "\n";
}
