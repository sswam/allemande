#!/usr/bin/perl
# NOTE: this will preserve options without separate arguments, and all options before --
# It will not work with options having separate arguments, and no --, as that is impossible without knowing the tool.
# Allemande shell tools use -f= for that reason.
use strict;
use warnings;
my $prog = shift;
my @opts = ();

my $dashdash_ix;
for (my $i = 0; $i < @ARGV; $i++) {
	if ($ARGV[$i] eq '--') {
		$dashdash_ix = $i;
		last;
	}
}

if (defined $dashdash_ix) {
	push @opts, splice(@ARGV, 0, $dashdash_ix);
	shift @ARGV; # remove --
} else {
	while (@ARGV && $ARGV[0] =~ /^-/) {
		push @opts, shift @ARGV;
	}
}
if (!@ARGV) {
	die "Usage: $0 program [options] arg1 [arg2 ...]";
}
push @ARGV, shift @ARGV;
exec $prog, @opts, @ARGV;

# todo skip options? or a version that does
