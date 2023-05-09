#!/usr/bin/perl -w
# k: extract columns

# extract columns from text input, and output tab-delimited text.

# usage: k <column1> <column2> <column3> < input_file.txt > output_file.txt

# example: k 2 1 3 < input_file.txt > output_file.txt

# This is similar to the standard unix tool cut, however:
# - it can reorder columns
# - it converts whitespace to tabs

# That latter "feature" is perhaps not so useful, but it is
# what I wanted at the time. It would be better to do that
# with a separate tool.

use strict;
my @slice = @ARGV;
my $line;
while (defined ($line = <STDIN>)) {
	chomp $line;
	$line =~ s/^\s*//;
	print join "\t", ('', split /\s+/, $line)[@slice];
	print "\n";
}
