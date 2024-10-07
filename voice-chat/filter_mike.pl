#!/usr/bin/perl -p
# Filter text from "mike" to correct common mishearings, if any...

use strict;
use warnings;
use utf8;
use open qw(:std :utf8);

BEGIN {
	$| = 1;
}

s{\bEllie\b}{Ally}g;

# s{\bTalia\b}{Thalia}g;
