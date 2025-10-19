#!/usr/bin/env perl

# ted.pl - apply transformations to text from STDIN as a whole

use strict;
use warnings;
use utf8;
use open qw(:std :utf8);

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
        eval $code;
        if ($@) {
            warn "Eval error: $@";
            return;
        }
    }

    print $_;
}

# Run the main function with all arguments as perl code
process_text(@ARGV);
