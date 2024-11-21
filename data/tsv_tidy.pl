#!/usr/bin/env perl
# Remove spaces around fields in a TSV file

use strict;
use warnings;

while ($_ = <STDIN>) {
	chomp;
	s/^ *//;	# Remove leading spaces
	s/ *\t/\t/g;	# Remove spaces before tabs
	s/\t */\t/g;	# Remove spaces after tabs
	s/ *$//;	# Remove trailing spaces
	print "$_\n";
}

