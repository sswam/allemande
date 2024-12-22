#!/usr/bin/env perl

use strict;
use warnings;
use autodie;
use v5.30;
use utf8;
use open qw(:std :utf8);
use Getopt::Long qw(GetOptions);
use Pod::Usage qw(pod2usage);
use FindBin qw($RealBin);
use lib "$RealBin/lib";
use ally::main qw(setup_logging get_logger io);

our $VERSION = '1.0.3';

# Set up command-line options
my %opts = (
    help => 0,
);

GetOptions(
    'help|h' => \$opts{help},
) or pod2usage(2);

pod2usage(-exitval => 0, -output => \*STDOUT, -noperldoc => 1, -verbose => 2) if $opts{help};

# Set up logging
setup_logging('ted');
my $logger = get_logger();

# Main function
sub process_text {
    my (@perl_code) = @_;

    # Read all of STDIN into $_
    local $/;  # Enable slurp mode
    $_ = <STDIN>;

    # Return unless we have input
    return unless defined $_;

    # Apply each code block in sequence
    for my $code (@perl_code) {
        $logger->info("Evaluating: $code");
        eval $code;
        if ($@) {
            $logger->error("Eval error: $@");
            return;
        }
    }

    print $_;
}

# Run the main function with all arguments as perl code
process_text(@ARGV);

__END__

=head1 NAME

ted.pl - Apply Perl code to STDIN and output to STDOUT

=head1 SYNOPSIS

ted.pl [options] 'perl-code' ['perl-code2' 'perl-code3' ...]

Options:
--help    Show this help message

=head1 DESCRIPTION

This script reads the entirety of STDIN into $_, applies the given Perl code
in sequence, and outputs the result to STDOUT. 
Simple transformations like s/foo/bar/ will work directly.

=head1 EXAMPLES

 Basic substitution:
     echo "hello world" | ted.pl 's/world/universe/'
     # Output: hello universe

 Multiple operations:
     echo "hello world" | ted.pl 's/world/universe/' 'tr/a-z/A-Z/'
     # Output: HELLO UNIVERSE

 Custom code:
     echo "hello world" | ted.pl '$_ = scalar reverse $_'
     # Output: dlrow olleh

=cut
