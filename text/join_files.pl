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
use File::Basename qw(basename);

our $VERSION = '1.0.1';

my %opts = (
    help => 0,
);

GetOptions(
    'help|h' => \$opts{help},
) or pod2usage(2);

pod2usage(-verbose => 2) if $opts{help};

my $sep = $ENV{JF_SEP} || '#File:';

my $dest = shift @ARGV or pod2usage("No destination file specified.\n");

if (-e $dest && (! -f $dest || -s $dest && index(IO::File->new($dest)->getline(), "$sep ") != 0)) {
    die "Would clobber: $dest\n";
}

my $destfh = IO::File->new(">$dest") or die "Cannot open $dest: $!\n";

while (my $src = shift @ARGV) {
    chomp $src;
    if (-T $src) {
        my $srcfh = IO::File->new($src) or die "Cannot open $src: $!\n";
        print $destfh $sep, ' ', $src, "\n";
        while (my $line = <$srcfh>) {
            if (index($line, $sep) == 0) {
                substr $line, length($sep), 0, '-';
            }
            unless ( substr( $line, length($line) - 1 ) eq "\n" ) {
                # oh no, doesn't end in a newline
                warn "\tAdding newline at EOF: $src\n";
                $line .= "\n";
            }
            print $destfh $line;
        }
    } elsif (-d $src) {
        opendir my $dh, $src or die "Error: Cannot open directory $src: $!\n";
        push @ARGV, map { "$src/$_" } grep { !/^\.\.?$/ } readdir $dh;
        closedir $dh;
    } else {
        warn "Ignoring $src\n";
    }
}

close $destfh;

__END__

=head1 NAME

join_files.pl - Join multiple files into a single file

=head1 SYNOPSIS

join_files.pl [options] <output_file> [input_file ...]

 Options:
   --help    Show this help message

=head1 DESCRIPTION

This script joins multiple input files into a single output file, adding a
separator line before the content of each file. It can process text files and
directories recursively.

=cut
