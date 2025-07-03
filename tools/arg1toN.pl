#!/usr/bin/perl
use strict;
use warnings;
my $prog = shift;
my @args = @ARGV;
push @args, shift @args;
exec $prog, @args;

# todo skip options? or a version that does
