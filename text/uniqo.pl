#!/usr/bin/perl -n

# `uniqo' - like uniq, but it works on unsorted files, and preserves the order of lines
# Usage: uniqo [-b] [-s] [file...]
# Options:
#   -b  include all blank lines
#   -B  remove all blank lines
#   -s  squeeze blank lines (implies -b)
# Example: uniqo -b input.txt > output.txt

our $opt_b;
our $opt_B;
our $opt_s;
our $prev_blank;
our %already;

BEGIN {
	use Getopt::Std;
	getopts('bBs');
	if ($opt_s) {
		$opt_b = 1;  # -s implies -b
	}
	@ARGV = ();  # Clear @ARGV to allow reading from STDIN if no files specified
	$prev_blank = 1;  # Initialize previous line as blank
}

# Process blank lines if -b option is set
if ($opt_B && /^$/) {
} elsif ($opt_b && /^$/) {
	if (!($opt_s && $prev_blank)) {
		print;
		$prev_blank = 1;
	}
} elsif (! exists $already{$_}) {
	# Process non-blank lines or all lines if -b is not set
	undef $already{$_};  # Mark line as seen
	print;  # Print unique line
	$prev_blank = 0;
}
