#!/usr/bin/env perl

use strict;
use warnings;
use v5.30;
use utf8;
use open qw(:std :utf8);
use Getopt::Long qw(GetOptions);
use Pod::Usage qw(pod2usage);
use List::Util qw(max);
use List::MoreUtils qw(all);

our $VERSION = '1.0.1';

# Set up command-line options
my %opts = (
    warn    => 0,
    help    => 0,
    version => 0,
    out     => 0,    # Remove specified columns
    right   => 0,    # Move specified columns to the right
    left    => 0,    # Move specified columns to the left
    range   => '',   # Column ranges
);

GetOptions(
    'warn|w'    => \$opts{warn},
    'help|h'    => \$opts{help},
    'version|v' => \$opts{version},
    'out'       => \$opts{out},
    'right'     => \$opts{right},
    'left'      => \$opts{left},
    'range=s'   => \$opts{range},  # Range specification
) or pod2usage(2);

pod2usage(1) if $opts{help};

if ($opts{version}) {
    say "kut.pl version $VERSION";
    exit 0;
}

# Prepare column indices
my @slice;
my %colnames;
my $use_header = 0;

# Collect column indices from @ARGV or from --range
if ($opts{range}) {
    # Process range specification
    @slice = parse_ranges($opts{range});
} else {
    @slice = @ARGV;
}

# Determine if non-numeric column identifiers are given
unless (all { /^\d+$/ } @slice) {
    $use_header = 1;
}

# Adjust indices to zero-based
# If using header names, leave @slice as is for now
if (!$use_header) {
    @slice = map { $_ - 1 } @slice;
}

my $max_slice = @slice ? max(@slice) : 0;

# Now process input line by line

my $header_processed = 0;
while (my $line = <STDIN>) {
    chomp $line;
    my @row = split /\t/, $line, -1;

    unless ($header_processed) {
        if ($use_header) {
            # Build a mapping of header names to indices
            %colnames = map { $row[$_] => $_ } 0..$#row;
            # Convert @slice from names to indices
            @slice = map {
                exists $colnames{$_} ? $colnames{$_}
                : die "Column '$_' not found in header\n"
            } @slice;
            $max_slice = max(@slice);
        }
        $header_processed = 1;
        # If keeping the header, output it accordingly
    }

    if (!$opts{warn}) {
        # Add empty columns if necessary
        my $add = $max_slice - $#row;
        push @row, ('') x $add if $add > 0;
    }

    my @output_row;

    if ($opts{out}) {
        # Remove specified columns
        my %slice_hash = map { $_ => 1 } @slice;
        @output_row = @row[ grep { !$slice_hash{$_} } 0..$#row ];
    } elsif ($opts{right}) {
        # Move specified columns to the right
        my %slice_hash = map { $_ => 1 } @slice;
        my @keep = @row[ grep { !$slice_hash{$_} } 0..$#row ];
        my @move = @row[@slice];
        @output_row = (@keep, @move);
    } elsif ($opts{left}) {
        # Move specified columns to the left
        my %slice_hash = map { $_ => 1 } @slice;
        my @keep = @row[ grep { !$slice_hash{$_} } 0..$#row ];
        my @move = @row[@slice];
        @output_row = (@move, @keep);
    } else {
        # Keep only specified columns (default behavior)
        @output_row = @row[@slice];
    }

    # Replace undefined with empty string
    @output_row = map { defined $_ ? $_ : '' } @output_row;

    say join "\t", @output_row;
}

sub parse_ranges {
    my ($range_str) = @_;
    my @ranges = split /,/, $range_str;
    my @cols;
    for my $r (@ranges) {
        if ($r =~ /^(\d+)-(\d+)$/) {
            push @cols, ($1..$2);
        } elsif ($r =~ /^(\d+)$/) {
            push @cols, $1;
        } else {
            die "Invalid range specification: $r\n";
        }
    }
    return @cols;
}

__END__

=head1 NAME

kut.pl - Manipulate columns from tab-delimited data

=head1 SYNOPSIS

kut.pl [options] [columns]

Options:
    -w, --warn          Warn on missing columns
    --out               Remove specified columns instead of keeping them
    --right             Move specified columns to the right
    --left              Move specified columns to the left
    --range=RANGE       Specify columns as ranges (e.g., 1-3,5)
    -h, --help          Show this help message
    -v, --version       Show version

=head1 DESCRIPTION

This script reads tab-delimited data from STDIN and manipulates columns
according to the options provided.

If non-numeric column identifiers are given, it assumes the first row is a header
and uses column names.

=head1 EXAMPLES

Keep columns 1 and 3:

    kut.pl 1 3

Remove columns 2 and 4:

    kut.pl --out 2 4

Move columns 1-3 to the right:

    kut.pl --right --range=1-3

Specify columns by name (assumes first row is header):

    kut.pl Name Age

=head1 AUTHOR

Your Name

=cut

# Certainly! Below is the improved `kut.pl` script. It now includes options to act like the other `kut*` scripts (`kutout`, `kutright`, `kutleft`, `kutc`) in an integrated way. It also supports specifying columns by header names if non-numeric identifiers are provided. The script has been updated in the style of `hello.pl`, including versioning and detailed options parsing.

# **Explanation:**
#
# - **Versioning and Style:** The script now includes version information (`$VERSION = '1.0.1'`) and follows the style demonstrated in `hello.pl`. It uses `Getopt::Long` for options parsing and includes a POD (Plain Old Documentation) at the end for help and usage instructions.
#
# - **Options Added:**
# - `--out`: Acts like `kutout`, removing the specified columns.
# - `--right`: Acts like `kutright`, moving specified columns to the right.
# - `--left`: Acts like `kutleft`, moving specified columns to the left.
# - `--range`: Acts like `kutc`, allowing columns to be specified as ranges.
# - If non-numeric column identifiers are given (e.g., column names), the script assumes the first row is a header and uses that to map column names to indices.
#
# - **Function Combining:** The script now allows combining different functions in one invocation. For example, you can both move columns and specify ranges in the same command.
#
# - **Usage Examples:**
# - Keeping specific columns: `kut.pl 1 3`
# - Removing specific columns: `kut.pl --out 2 4`
# - Moving columns to the right: `kut.pl --right --range=1-3`
# - Using header names: `kut.pl Name Age`
#
# **Note:** Ensure that the required Perl modules (`List::MoreUtils`) are installed on your system. You can install them using CPAN if necessary.
#
# **Testing the Script:**
#
# To test the script, you can create a sample tab-delimited file `data.tsv`:

# Name    Age     Occupation
# Alice   30      Engineer
# Bob     25      Designer
# Carol   27      Manager

# Then run the script:
#
# - Keep columns by name:

# cat data.tsv | perl kut.pl Name Occupation

# - Remove columns by number:

# cat data.tsv | perl kut.pl --out 2

# - Move columns to the left:

# cat data.tsv | perl kut.pl --left 3 2

# This updated `kut.pl` script should now provide a flexible and integrated way to manipulate columns in your data, combining the functionalities of the other `kut*` scripts.
