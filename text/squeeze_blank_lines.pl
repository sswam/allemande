#!/usr/bin/perl -nw
# squeeze-blank-lines: Remove mulitple blank lines from a file

use strict;
use warnings;

our ($max_blank, $max_top_blank, $blank_count, $at_top);

BEGIN {
	($max_blank, $max_top_blank) = @ARGV;
	$max_blank = 1 if !defined $max_blank;
	$max_top_blank = 0 if !defined $max_top_blank;
	$blank_count = 0;
	$at_top = 1;
	@ARGV = ();
}

print unless /^$/ && $blank_count >= ($at_top ? $max_top_blank : $max_blank);
$blank_count++ if /^$/;
$blank_count = 0, $at_top = 0 if !/^$/;
