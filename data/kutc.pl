#!/usr/bin/perl -p

# kutc: cut columns from a file, converting it to TSV
# Usage: kutc <range1>[,<range2>,...] < input_file
# Example: kutc 1-3,5-7 < input.txt

BEGIN {
	# Process command-line arguments
	$arg = join ",", @ARGV;
	for (split /,/, $arg) {
		($from, $to) = split /-/, $_;
		push @ranges, [$from, $to];
	}
	@ARGV = ();  # Clear @ARGV to allow reading from STDIN
}

chomp;  # Remove newline from input line

$out = "";
for $r (@ranges) {
	# Extract columns based on specified ranges
	($from, $to) = @$r;
	$from ||= 1; $to ||= length($_);  # Default values if not specified
	$out .= substr($_, $from-1, $to-$from+1)."\t";
}
$out =~ s/\t$//;  # Remove trailing tab

$_ = "$out\n";  # Set output line with newline
