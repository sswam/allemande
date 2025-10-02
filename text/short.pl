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
use ally::main qw(io);
# use ally::main qw(setup_logging get_logger io);

our $VERSION = '1.0.1';

# Set up command-line options
my %opts = (
    maxlen     => 300,
    show_long  => 0,
    help       => 0,
);

GetOptions(
    'c'        => \$opts{show_long},
    'help|h'   => \$opts{help},
) or pod2usage(2);

pod2usage(-exitval => 0, -output => \*STDOUT, -noperldoc => 1, -verbose => 2) if $opts{help};

# # Set up logging
# setup_logging('short');
# my $logger = get_logger();

# Process command line args
$opts{maxlen} = $ARGV[0] if @ARGV;

sub process_lines {
    my ($input, $output) = @_;
    my ($get, $put) = io($input, $output);

    while (my $line = $get->()) {
        chomp $line;

        if (length($line) > $opts{maxlen}) {
            if ($opts{show_long}) {
                $put->($line . "\n");
            } else {
                $put->(substr($line, 0, $opts{maxlen}) . " ...\n");
            }
        } elsif (!$opts{show_long}) {
            $put->($line . "\n");
        }
    }
}

# Run main function
process_lines(\*STDIN, \*STDOUT);

__END__

=head1 NAME

short.pl - filter short and long lines in input

=head1 SYNOPSIS

short.pl [maxlen] [-c]

Options:
-c            Show only lines longer than maxlen
--help        Show this help message

=head1 DESCRIPTION

This script processes input lines and either shows them truncated at maxlen
characters (default behavior) or shows only the lines longer than maxlen
when -c is specified.

=cut
