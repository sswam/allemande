#!/usr/bin/env perl
use strict;
use warnings;
use File::Slurp 'slurp';

my %opt;
my %map;
my $multiline = 0;

# sub A A-new B B-new
# sub -e

# -w  word
# -e  environment
# -d  debug
# -q%% quote
# -m=file map 'file'
# -r  reverse
# -f  from/to args are files

while (($ARGV[0]//'') =~ /^-(.)(.*)/) {
	$opt{$1} = $2;
	shift @ARGV;
}

if (exists $opt{e}) {
	unshift @ARGV, %ENV;
}
my ($q0,$q1) = split //, ($opt{q}//"");
for ($q0,$q1) { $_//=""; }
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

if ($multiline) {
	undef $/;
}

while (defined ($_ = <STDIN>)) {
	s/($rx)/$map{$1}/ge if $rx ne '';
	print;
}
