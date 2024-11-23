#!/usr/bin/env perl

use strict;
use warnings;
use autodie;
use v5.30;
use utf8;
use open qw(:std :utf8);
use Getopt::Long qw(GetOptions);
use Pod::Usage qw(pod2usage);
use IO::File;

our $VERSION = '1.0.1';

my %opts = (
    help => 0,
);

GetOptions(
    'help|h' => \$opts{help},
    'test|n' => \$opts{test},
) or pod2usage(2);

pod2usage(-exitval => 0, -output => \*STDOUT, -noperldoc => 1, -verbose => 2) if $opts{help};

my $sep = $ENV{JF_SEP} || '#File:';

my $src = shift or pod2usage("usage: $0 all.txt\nsee: join-files\n");

my $srcfh = IO::File->new($src) or die "cannot open $src\n";

my $line;
while (1) {
    $line = <$srcfh>;
    last if !defined $line || index($line, "$sep ") == 0;
    chomp $line;
    warn "skipping line: $line\n";
}

my @dests;

do {
    my $dest;
    chomp($dest = substr $line, length($sep) + 1);

    if ($dest eq $src) {
        die "Error: Target file '$dest' cannot be the input files.\n";
    }

    if (-e "$dest~") {
        system "move-rubbish", "$dest~" or die "Could not move $dest~ to rubbish\n";
    }
    rename $dest, "$dest~" if -e $dest;

    my $i = -1;
    while (($i = index $dest, '/', $i + 1) != -1) {
        my $dir = substr $dest, 0, $i;
        unless ($dir eq "" || -d $dir) {
            mkdir $dir, 0777 or die "cannot mkdir $dir\n";
        }
    }

    my $destfh = IO::File->new(">>$dest") or die "cannot open $dest\n";

    push @dests, $dest;

    while (defined($line = <$srcfh>)) {
        if (index($line, $sep) == 0) {
            last if index($line, "$sep ") == 0;
            $line = $sep . substr $line, length($sep) + 1;
        }
        print $destfh $line;
    }

    close $destfh;
} while (defined $line);

foreach my $dest (@dests) {
    if (-e "$dest~" && !system "cmp", "-s", $dest, "$dest~") {
        print "= $dest\n";
        rename "$dest~", $dest;
    }
    else {
        print "> $dest\n";
        if ($opts{test}) {
            unlink $dest;
            if (-e "$dest~") {
                rename "$dest~", $dest;
            }
        }
        elsif (-e "$dest~") {
            system "chmod", "--reference=$dest~", $dest;
        }
    }
}

__END__

=head1 NAME

split-files - Split joined files into separate files

=head1 SYNOPSIS

split-files [options] all.txt

 Options:
   --test, -n     Test mode, do not modify files
   --help         Show this help message

=head1 DESCRIPTION

This script splits a joined file (created by join-files utility) into separate files.
It works in conjunction with the 'join-files' utility to facilitate global search / replace, etc.

=cut
