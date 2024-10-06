#!/usr/bin/perl -w
# section_make:        replace template variables with values
# example usage: ./section_make template/section.txt section_uc STAY section_lc stay section_tc Stay section_kc stay section_uc_spaced STAY > stay.txt

use strict;
use warnings;

my ($template, %map) = @ARGV;

open my $fh, '<', $template or die "Can't open $template: $!\n";

sub replace {
	my $key = shift;
	return $map{$key} if exists $map{$key};
	warn "No replacement for $key\n";
	return "\${$key}";
}

while (<$fh>) {
	s/\$\{(.*?)\}/replace($1)/ge;
	print;
}
