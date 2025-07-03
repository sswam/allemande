#!/usr/bin/perl
use strict;
use warnings;
my $prog = shift;
my @args = @ARGV;
unshift @args, pop @args;
exec $prog, @args;

# todo skip options? or a version that does
