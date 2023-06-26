#!/usr/bin/perl -p
# markdown_number_headings.pl: Number 2nd-level headings in a Markdown document.
use strict;
use warnings;

our $i;

BEGIN {
	$i = 1;
}

if (/^## /) {
	s/^## /## $i. /;
	$i++;
}
