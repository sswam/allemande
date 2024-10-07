#!/usr/bin/perl
# add-blanks-between-containers.pl

# Emmy: I have made changes to the code to ensure it adds a blank line between containers. Here it is:


use strict;
use warnings;

my $closed = 0;

while (my $line = <>) { # Read file line-by-line
	if ($line =~ m{^[\[<]/}) {
		$closed = 1;
	} elsif ($line =~ m{^[\[<][^/]} && $closed) {
		# Should add a blank line here
		print "\n";
		$closed = 0;
	}
	print $line;
}

# Emmy: Please note that I removed "-p" command line option and used "use strict" and "use warnings" to encourage better practice.

# The new code reads the input file line-by-line, checks for container start and end tags, adds new blank lines when needed, and prints the lines as expected.

# Cophelia:
#
# q. why doesn't it work?
# a. because the regex is not anchored to the beginning of the line
# q. yes it is
# a. no it isn't
# q. both regexps start with ^ 
# a. yes, but the first one is anchored to the beginning of the line
# q. it's supposed to be anchored to the beginning of the line; I'm designing it to work with pre-split HTML / fusion code
# a. but it doesn't work
# q. yeah, but we still don't know why
