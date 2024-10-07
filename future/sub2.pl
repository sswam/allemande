#!/usr/bin/env perl

# This script performs text substitution based on various options and a mapping.
# It reads from STDIN and writes to STDOUT.
# Options:
#   -w: Match whole words only
#   -e: Use environment variables as mapping
#   -d: Debug mode (print regex)
#   -q: Specify quote characters for keys
#   -m: Read mapping from file
#   -r: Reverse key-value pairs
#   -f: Treat key-value pairs as filenames and read their contents

use strict;
use warnings;
use File::Slurp 'slurp';

my %opt;
my %map;
my $multiline = 0;

# Parse command-line options
while (($ARGV[0]//'') =~ /^-(.)(.*)/) {
	$opt{$1} = $2;
	shift @ARGV;
}

# Use environment variables if -e option is set
if (exists $opt{e}) {
	unshift @ARGV, %ENV;
}

# Set up quote characters for keys
my ($q0,$q1) = split //, ($opt{q}//"");
for ($q0,$q1) { $_//=""; }

# Read mapping from file if -m option is set
if (exists $opt{m}) {
	$opt{m} =~ s/^=//;
	open my $fh, '<', $opt{m}
		or die "can't open map file: $opt{m}\n";
	while (<$fh>) {
		chomp;
		my ($k, $v) = split /\t/, $_, -1;
		push @ARGV, $k, $v;
	}
	close $fh;
}

# Process key-value pairs
while (my ($k, $v) = splice(@ARGV, 0, 2)) {
	if (exists $opt{r}) {
		($k, $v) = ($v, $k);
	}
	if (exists $opt{f}) {
		$k = slurp($k);
		$v = slurp($v);
	}
	$k = "$q0$k$q1";
	$map{$k} = $v;
}

# Build regex for substitution
my $rx = '';
for my $k (keys %map) {
	if ($k =~ /\n/) {
		$multiline = 1;
	}
	my $x = quotemeta($k);
	$x = "\\b$x\\b" if exists $opt{w};
	$rx .= '|' if $rx;
	$rx .= $x;
}
$rx = qr{$rx} if $rx ne '';
warn "$rx\n" if exists $opt{d};

# Set input record separator for multiline mode
if ($multiline) {
	undef $/;
}

# Process input and perform substitutions
while (defined ($_ = <STDIN>)) {
	s/($rx)/$map{$1}/ge if $rx ne '';
	print;
}
