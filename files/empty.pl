#!/usr/bin/env perl

use strict;
use warnings;
use autodie;
use v5.30;
use utf8;
use open         qw(:std :utf8);
use Getopt::Long qw(GetOptions);
use Pod::Usage   qw(pod2usage);
use FindBin      qw($RealBin);
use lib "$RealBin/lib";
use ally::main qw(setup_logging get_logger);

our $VERSION = '1.0.0';

# Set up command-line options
my %opts = (
    help => 0,
);

GetOptions(
    'help|h' => \$opts{help},
) or pod2usage(2);

pod2usage(-exitval => 0, -output => \*STDOUT, -noperldoc => 1, -verbose => 2) if $opts{help};

# Set up logging
setup_logging('empty');
my $logger = get_logger();

# Main function
sub check_empty {
    my @files = @_;

    for my $file (@files) {
        my $size = -s $file;

        if (!defined $size || $size == 0) {
            say $file;
            next;
        }

        if ($size < 1024) {
            open my $fh, '<', $file;
            my $content = do { local $/; <$fh> };
            close $fh;

            if ($content =~ /^\s*$/) {
                say $file;
            }
        }
    }
}

# Run the main function
check_empty(@ARGV);

__END__

=head1 NAME

empty.pl - Check if files are empty or contain only whitespace (<1KB)

=head1 SYNOPSIS

empty.pl [options] [files...]

Options:
--help         Show this help message

=head1 DESCRIPTION

This script checks if files are empty (0 bytes) or less than 1KB and contain
only whitespace. Matching files are printed to stdout, one per line.

=cut
