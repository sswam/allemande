#!/usr/bin/perl

for $hms (@ARGV) {
	my $sign = $hms =~ s/^-// ? -1 : 1;
	($s, $m, $h) = reverse split /:/, $hms;
	print $sign * ($s + $m*60 + $h*3600), "\n";
}
