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
use ally::main qw(setup_logging get_logger io);

our $VERSION = '0.1.0';

# Set up command-line options
my %opts = (
    help => 0,
);

GetOptions(
    'help|h' => \$opts{help},
) or pod2usage(2);

pod2usage(-exitval => 0, -output => \*STDOUT, -noperldoc => 1, -verbose => 2) if $opts{help};

# Set up logging
setup_logging('joined_files');
my $logger = get_logger();

# Main function
sub joined_files {
    my ($input, $output) = @_;

    my ($get, $put) = io($input, $output);

    my $sep = $ENV{JF_SEP} || '#File:';

    while (my $line = $get->()) {
        if (index($line, "$sep ") == 0) {
            my $filename = substr($line, length($sep) + 1);
            chomp $filename;
            $put->($filename);
        }
    }
}

# Run the main function
joined_files(\*STDIN, \*STDOUT);

__END__

=head1 NAME

joined_files.pl - List files included in a joined file

=head1 SYNOPSIS

joined_files.pl [options]

 Options:
   --help         Show this help message

=head1 DESCRIPTION

This script lists the files included in a joined file, one filename per line,
without any additional output.

=cut
