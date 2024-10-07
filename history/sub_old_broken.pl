#!/usr/bin/env perl


use strict;
use warnings;
use v5.30;
use utf8;
use open qw(:std :utf8);
use Getopt::Long qw(GetOptions);
use Pod::Usage qw(pod2usage);
use File::Slurp 'slurp';

our $VERSION = '1.0.0';

my %opt;
my %map;
my $multiline = 0;

# Set up command-line options
GetOptions(
    'w' => \$opt{w},
    'e' => \$opt{e},
    'd' => \$opt{d},
    'q=s' => \$opt{q},
    'm=s' => \$opt{m},
    'r' => \$opt{r},
    'f' => \$opt{f},
    'help|h' => sub { pod2usage(1) },
) or pod2usage(2);

# Main substitution logic
sub perform_substitution {
    # Use environment variables if -e option is set
    if (exists $opt{e}) {
        unshift @ARGV, %ENV;
    }

    # Set up quote characters for keys
    my ($q0,$q1) = split //, ($opt{q}//"");
    for ($q0,$q1) { $_//=""; }

    # Read mapping from file if -m option is set
    if (exists $opt{m}) {
        $opt{m} =~ s/^=//;
        open my $fh, '<', $opt{m}
            or die "can't open map file: $opt{m}\n";
        while (<$fh>) {
            chomp;
            my ($k, $v) = split /\t/, $_, -1;
            push @ARGV, $k, $v;
        }
        close $fh;
    }

    # Process key-value pairs
    while (my ($k, $v) = splice(@ARGV, 0, 2)) {
        if (exists $opt{r}) {
            ($k, $v) = ($v, $k);
        }
        if (exists $opt{f}) {
            $k = slurp($k);
            $v = slurp($v);
        }
        $k = "$q0$k$q1";
        $map{$k} = $v;
    }

    # Build regex for substitution
    my $rx = '';
    for my $k (keys %map) {
        if ($k =~ /\n/) {
            $multiline = 1;
        }
        my $x = quotemeta($k);
        $x = "\\b$x\\b" if exists $opt{w};
        $rx .= '|' if $rx;
        $rx .= $x;
    }
    $rx = qr{$rx} if $rx ne '';
    warn "$rx\n" if exists $opt{d};

    # Set input record separator for multiline mode
    if ($multiline) {
        undef $/;
    }

    # Process input and perform substitutions
    while (defined ($_ = <STDIN>)) {
        s/($rx)/$map{$1}/ge if $rx ne '';
        print;
    }
}

# Run the main function
perform_substitution();

__END__

=head1 NAME

sub.pl - A script for text substitution with various options

=head1 SYNOPSIS

sub.pl [options] [key value ...]

Options:

    -w             Match whole words only
    -e             Use environment variables as mapping
    -d             Debug mode (print regex)
    -q CHARS       Specify quote characters for keys
    -m FILE        Read mapping from file
    -r             Reverse key-value pairs
    -f             Treat key-value pairs as filenames and read their contents
    --help|-h      Show this help message

=head1 DESCRIPTION

This script performs text substitution based on various options and a mapping.
It reads from STDIN and writes to STDOUT.

=head1 EXAMPLES

Basic substitution:
    echo "Hello world" | ./sub.pl Hello Goodbye

Whole word matching:
    echo "Hello world" | ./sub.pl -w He She

Use environment variables:
    export FOO=bar
    ./sub.pl -e < input.txt

Debug mode:
    echo "Test" | ./sub.pl -d key value

Custom quote characters:
    echo "<<key>>" | ./sub.pl -q<> key value

Read mapping from file:
    echo "content" | ./sub.pl -m=mapfile.txt

Reverse key-value pairs:
    echo "reverse this" | ./sub.pl -r value key

Treat key-value pairs as filenames:
    echo "replace" | ./sub.pl -f key.txt value.txt

Combine options:
    echo "complex example" | ./sub.pl -wed -q<> -m=mapfile.txt -r -f

=cut

# Here's an improved version of `sub.pl` incorporating a help option and usage information, styled similarly to `hello.pl`:

# This improved version of `sub.pl` now includes:
#
# 1. A help option (`--help` or `-h`) that displays usage information.
# 2. Usage of `GetOptions` for more robust command-line option parsing.
# 3. A `pod2usage` call to display help information.
# 4. A `__END__` section with POD documentation, including a description of the script, its options, and usage examples.
# 5. The main substitution logic moved into a separate subroutine for better organization.
#
# These changes make the script more user-friendly and align its style more closely with `hello.pl`.
