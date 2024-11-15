#!/usr/bin/env perl

use strict;
use warnings;
use autodie;
use v5.30;
use utf8;
use open         qw(:std :utf8);
use Getopt::Long qw(GetOptions);
use Pod::Usage   qw(pod2usage);
use Email::Simple;
use FindBin qw($RealBin);
use lib "$RealBin/lib";
use ally::main qw(setup_logging get_logger io);
use List::Util qw(first max maxstr min minstr reduce shuffle sum);
use Encode qw(decode encode);

our $VERSION = '1.0.1';

# Set up command-line options
my %opts = (
    fields => '',
    cut    => '',
    filter => 0,
    debug  => 0,
    help   => 0,
);

GetOptions(
    'fields=s' => \$opts{fields},
    'cut=s'    => \$opts{cut},
    'filter'   => \$opts{filter},
    'debug'    => \$opts{debug},
    'help|h'   => \$opts{help},
) or pod2usage(2);

pod2usage( -exitval => 0, -output => \*STDOUT, -noperldoc => 1, -verbose => 2 )
  if $opts{help};

# Set up logging
setup_logging('headersproc');
my $logger = get_logger();

# Main function
sub headersproc {
    my ( $input, $output ) = @_;
    my ( $get,   $put )    = io( $input, $output );

    # Read all input into a buffer
    my $buffer = '';
    while ( my $line = $get->() ) {
        $buffer .= $line;
    }

    # Split into records (double newline separator)
    my @records = split( /\n\n+/, $buffer );

    # Process each record
    foreach my $record (@records) {
        next unless $record =~ /\S/;    # Skip empty records

        my $message = Email::Simple->new($record);

        # Get all headers as a hash
        my %headers;
        foreach my $header ( $message->header_names ) {
            my $value = $message->header($header);
            # Ensure proper UTF-8 encoding for output
            $value = encode('UTF-8', decode('UTF-8', $value, Encode::FB_CROAK));
            $headers{ lc $header } = $value;
        }

        # Output in a simple format
        foreach my $key ( sort keys %headers ) {
            $put->(encode('UTF-8', "$key: $headers{$key}\n"));
        }
        $put->("\n");    # Record separator
    }
}

headersproc( \*STDIN, \*STDOUT );

__END__

=head1 NAME

headersproc.pl - Process Debian/APT style header files

=head1 SYNOPSIS

headersproc.pl [options] [program]

Options:
--fields FIELDS  Comma-separated list of fields to output
--cut FIELDS    Comma-separated list of fields to exclude
--filter        Filter mode (TBD)
--debug         Show debug information
--help          Show this help message

=head1 DESCRIPTION

This script processes files in RFC 2822 header format (like Debian package lists).

=cut

# TODO:
# - warning: UTF-8 "\xFC" does not map to Unicode  when processing /var/lib/apt/lists/deb.debian.org_debian_dists_bookworm_main_binary-amd64_Packages
# - Combine with csvproc and make it work for various different record-based formats
# - Process record by record, don't read the whole file up front
# - Output in similar rfc-2822 format by default
# - Preserve field order in output
# - Implement field selection based on --fields option
# - Implement field exclusion based on --cut option
# - Add more sophisticated filtering capabilities
# - Consider adding format options for output
# - Add support for different output formats (JSON, YAML, etc.)
